"""Builds data/layout.json: the schematic CTABot map, made from data/stations.json.

How the drawing is made, so it can be checked and rebuilt:
 1. Stations start at their real positions, with downtown enlarged (a "fisheye") so the Loop is readable.
 2. Every stretch of track between two stations is turned to the nearest of 8 directions (H, V, 45 deg),
    and a least-squares fit moves stations as little as possible to make that true. Real geography wins
    wherever the two disagree a lot (soft constraints, not forced).
 3. Express runs (e.g. Purple Express skipping Red Line stops) are routed along the track they really use,
    so they draw as parallel lines beside the local line instead of a separate straight cut.

Run: python tools/build_layout.py   (no network needed)
"""
import json, math
from collections import defaultdict
import numpy as np

CENTER = (41.8817, -87.6278)          # State & Madison, the zero point of Chicago's street grid
FISH_S, FISH_P = 1.2, 0.62            # fisheye: radius (km) where shrinking starts, and how strong
MIN_GAP = 22.0                        # shortest drawn distance between neighbouring stations
DIRS = [(math.cos(k * math.pi / 4), math.sin(k * math.pi / 4)) for k in range(8)]
# Downtown is hand-placed on a grid (map units, Loop centre = 0,0; the Loop is a 120 x 120 square):
# automatic layout can't make the Loop readable, which is why CTA's own map draws downtown by hand too.
# Everything else follows real geography. Names must match CTA's station names exactly (checked below).
PINS = {
    # the Loop: Lake St (top), Wabash (right), Van Buren (bottom), Wells (left)
    "Clark/Lake": (-35, -60), "Washington/Wabash": (60, -25), "Adams/Wabash": (60, 25),
    "Harold Washington Library-State/Van Buren": (35, 60), "LaSalle/Van Buren": (-10, 60),
    "Quincy": (-60, 25), "Washington/Wells": (-60, -25),
    # Red Line subway down State St
    "Clark/Division": (20, -175), "Chicago (Red)": (20, -135), "Grand (Red)": (20, -95), "Lake (Subway)": (20, -35),
    "Monroe (Red)": (20, 5), "Jackson (Red)": (20, 38), "Harrison": (20, 95), "Roosevelt": (60, 140),
    "Cermak-Chinatown": (20, 190), "Cermak-McCormick Place": (60, 190),
    # Blue Line subway down Dearborn, then west on the Congress branch
    "Chicago (Blue)": (-125, -150), "Grand (Blue)": (-90, -115), "Washington": (-35, -25),
    "Monroe (Blue)": (-35, 5), "Jackson (Blue)": (-35, 38), "LaSalle": (-35, 90), "Clinton (Blue)": (-95, 90),
    "UIC-Halsted": (-150, 90),
    # Brown/Purple north of the Loop, Green/Pink west on Lake St
    "Merchandise Mart (Brown/Purple)": (-60, -110), "Chicago (Brown/Purple)": (-60, -150), "Sedgwick (Brown/Purple)": (-60, -190),
    # the shared 4-track north side: Brown/Purple straight up Sheffield, Red peels off into the subway at Fullerton
    "Armitage (Brown/Purple)": (-85, -240), "Fullerton": (-85, -270), "North/Clybourn": (-35, -200),
    "Clinton (Green/Pink)": (-110, -60), "Morgan (Green/Pink)": (-160, -60), "Ashland (Green/Pink)": (-210, -60),
}
# Real junctions where tracks meet (no station there). Track between two stations is routed through them,
# so lines sharing real track draw as one neat bundle around the Loop's corners.
JUNCTIONS = {"J:Lake/Wells": (-60, -60), "J:Lake/Wabash": (60, -60), "J:Van Buren/Wabash": (60, 60), "J:Van Buren/Wells": (-60, 60)}
VIA = {   # (from, to): junctions passed, in order
    ("Merchandise Mart (Brown/Purple)", "Washington/Wells"): ["J:Lake/Wells"],
    ("Merchandise Mart (Brown/Purple)", "Clark/Lake"): ["J:Lake/Wells"],
    ("Clinton (Green/Pink)", "Clark/Lake"): ["J:Lake/Wells"],
    ("Clinton (Green/Pink)", "Washington/Wells"): ["J:Lake/Wells"],
    ("Clark/Lake", "Washington/Wells"): ["J:Lake/Wells"],
    ("Clark/Lake", "Washington/Wabash"): ["J:Lake/Wabash"],
    ("Adams/Wabash", "Harold Washington Library-State/Van Buren"): ["J:Van Buren/Wabash"],
    ("Adams/Wabash", "Roosevelt"): ["J:Van Buren/Wabash"],
    ("Harold Washington Library-State/Van Buren", "Roosevelt"): ["J:Van Buren/Wabash"],
    ("Quincy", "LaSalle/Van Buren"): ["J:Van Buren/Wells"],
}
ORDER = ["Purple", "Brown", "Orange", "Pink", "Green", "Red", "Blue", "Yellow"]   # side-by-side order in shared tracks


def km_xy(lat, lon):
    x = (lon - CENTER[1]) * 111.32 * math.cos(math.radians(CENTER[0]))
    y = -(lat - CENTER[0]) * 110.54                                       # screen y grows downward
    return x, y


def fisheye(x, y):
    r = math.hypot(x, y)
    if r < 1e-9:
        return 0.0, 0.0
    k = (1 + r / FISH_S) ** -FISH_P
    return x * k, y * k


def bend_path(p, q):
    """p -> q drawn as at most two pieces, each H, V or 45 deg. The bend goes on the outside (farther from the Loop)."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    ax, ay = abs(dx), abs(dy)
    if min(ax, ay) < 0.5 or abs(ax - ay) < 0.5:
        return [p, q]
    sx, sy = math.copysign(1, dx), math.copysign(1, dy)
    dg = min(ax, ay)
    straight_first = (p[0] + (dx - sx * dg), p[1] + (dy - sy * dg))      # straight part, then the 45 deg part
    diag_first = (p[0] + sx * dg, p[1] + sy * dg)                        # 45 deg part, then straight
    b = max((straight_first, diag_first), key=lambda c: math.hypot(*c))
    return [p, (round(b[0], 1), round(b[1], 1)), q]


def snap_dir(dx, dy):
    best = max(DIRS, key=lambda d: d[0] * dx + d[1] * dy)
    return best


def main():
    d = json.load(open("data/stations.json"))
    st = {s["id"]: s for s in d["stations"]}
    geo = {sid: km_xy(s["lat"], s["lon"]) for sid, s in st.items()}

    # ---- 1. which pairs of stations are directly connected, and by which lines
    direct = defaultdict(set)
    for line, pats in d["lines"].items():
        for p in pats:
            for a, b in zip(p["stations"], p["stations"][1:]):
                direct[frozenset((a, b))].add(line)

    graph = defaultdict(set)
    for e in direct:
        a, b = tuple(e); graph[a].add(b); graph[b].add(a)

    def gdist(a, b):
        return math.dist(geo[a], geo[b])

    def via_path(a, b):
        """A route from a to b through other stations that is almost as short as the direct hop (an express run)."""
        best = None; direct_len = gdist(a, b)
        stack = [(a, [a], 0.0)]
        while stack:
            u, path, L = stack.pop()
            if L > direct_len * 1.2 or len(path) > 14:
                continue
            for v in graph[u]:
                if v in path or (u == a and v == b):
                    continue
                L2 = L + gdist(u, v)
                if v == b:
                    if len(path) >= 2 and L2 <= direct_len * 1.2 and (best is None or L2 < best[1]):
                        best = (path + [b], L2)
                    continue
                stack.append((v, path + [v], L2))
        return best and best[0]

    # ---- 2. each line's drawn route: express hops replaced by the track they run on
    routes, edge_lines = {}, defaultdict(set)
    for line, pats in d["lines"].items():
        rs = []
        for p in pats:
            seq = [p["stations"][0]]
            for a, b in zip(p["stations"], p["stations"][1:]):
                others = direct[frozenset((a, b))] - {line}
                path = None if others else via_path(a, b)
                seq += (path[1:] if path else [b])
            full = [seq[0]]                                               # add the junctions each hop passes
            for a, b in zip(seq, seq[1:]):
                na, nb = st[a]["name"], st[b]["name"]
                via = VIA.get((na, nb)) or list(reversed(VIA.get((nb, na), [])))
                full += via + [b]
            seq = full
            rs.append({"stations": p["stations"], "drawn": seq, "trips": p["trips"]})
            for a, b in zip(seq, seq[1:]):
                edge_lines[frozenset((a, b))].add(line)
        routes[line] = rs

    ids = sorted({s for e in edge_lines for s in e})
    idx = {s: i for i, s in enumerate(ids)}
    names = {(st[s]["name"] if s in st else s): s for s in ids}
    bad = [n for n in list(PINS) + [n for k in VIA for n in k] if n not in names]
    if bad:
        raise SystemExit(f"Pinned stations not found in CTA's data (renamed or closed?): {bad}")
    pin = {idx[names[n]]: xy for n, xy in PINS.items()}
    pin.update({idx[j]: xy for j, xy in JUNCTIONS.items()})
    f = np.array([fisheye(*geo[s]) if s in geo else (0.0, 0.0) for s in ids])
    # scale + shift the fisheye so the pinned stations line up with their grid spots
    pi = [idx[names[n]] for n in PINS]; A = np.array([[f[i, 0], 1, 0] for i in pi] + [[f[i, 1], 0, 1] for i in pi])
    b = np.array([pin[i][0] for i in pi] + [pin[i][1] for i in pi])
    (scale, tx, ty), *_ = np.linalg.lstsq(A, b, rcond=None)
    p0 = f * scale + [tx, ty]
    # hand-placed stations pull their automatic neighbours along with them (fading with distance), so an area
    # moved by hand doesn't leave nearby stations behind on the wrong side of it
    SIGMA = 110.0
    real_pins = [idx[names[n]] for n in PINS]
    resid = {i: np.array(pin[i]) - p0[i] for i in real_pins}
    shifted = p0.copy()
    for j in range(len(ids)):
        if j in pin:
            continue
        g = np.array([math.exp(-np.sum((p0[j] - p0[i]) ** 2) / (2 * SIGMA ** 2)) for i in real_pins])
        shifted[j] = p0[j] + (g[:, None] * np.array([resid[i] for i in real_pins])).sum(0) / max(g.sum(), 1.0)
    p0 = shifted
    for i, xy in pin.items():
        p0[i] = xy
    print(f"fisheye scale {scale:.1f} units per km at the centre")
    edges = [tuple(sorted(e)) for e in edge_lines]

    # ---- 3. straighten: least squares, a few rounds (directions re-chosen from the last result)
    pos = p0.copy()
    for rnd in range(4):
        rows, rhs = [], []
        n = len(ids)
        def row():
            return np.zeros(2 * n)
        for i in range(n):                                              # stay near the real place (pins: stay put)
            wa = 60.0 if i in pin else 0.35
            for k in (0, 1):
                r = row(); r[2 * i + k] = wa; rows.append(r); rhs.append(wa * p0[i, k])
        for a, b in edges:
            i, j = idx[a], idx[b]
            if i in pin and j in pin:
                continue                                                # hand-placed: drawn with a 45 deg bend if needed
            v = pos[j] - pos[i]
            ux, uy = snap_dir(*v)
            nx, ny = -uy, ux
            w = 6.0
            r = row(); r[2*j] = w*nx; r[2*j+1] = w*ny; r[2*i] = -w*nx; r[2*i+1] = -w*ny; rows.append(r); rhs.append(0.0)
            along = max(ux * v[0] + uy * v[1], MIN_GAP)
            w2 = 1.2 if along > MIN_GAP * 1.5 else 9.0          # push hard on stretches that are getting too short
            r = row(); r[2*j] = w2*ux; r[2*j+1] = w2*uy; r[2*i] = -w2*ux; r[2*i+1] = -w2*uy; rows.append(r); rhs.append(w2 * along)
        sol, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)
        pos = sol.reshape(-1, 2)

    for i, xy in pin.items():
        pos[i] = xy
    # report how straight the result is (before bends are added)
    off = []
    for a, b in edges:
        v = pos[idx[b]] - pos[idx[a]]
        ang = math.degrees(math.atan2(v[1], v[0])) % 45
        off.append(min(ang, 45 - ang))
    off.sort()
    print(f"{len(ids)} stations, {len(edges)} track pieces; angle off H/V/45: median {off[len(off)//2]:.1f} deg, "
          f"95% {off[int(len(off)*.95)]:.1f} deg, worst {off[-1]:.1f} deg")
    short = sorted(math.dist(pos[idx[a]], pos[idx[b]]) for a, b in edges)
    print(f"shortest station gap {short[0]:.1f} units (target {MIN_GAP})")

    # tidy: round, and move so the map starts at 0,0
    pos -= pos.min(axis=0) - 40
    P = {s: (round(float(pos[idx[s], 0]), 1), round(float(pos[idx[s], 1]), 1)) for s in ids}
    loop_c = np.array(PINS["Clark/Lake"]) * 0 + (pos[idx[names["Clark/Lake"]]] - PINS["Clark/Lake"])
    def bp(a, b):
        p, q = np.array(P[a]) - loop_c, np.array(P[b]) - loop_c
        return [[round(x + loop_c[0], 1), round(y + loop_c[1], 1)] for x, y in bend_path(tuple(p), tuple(q))]
    def canon(a, b):
        pts = bp(a, b)
        (x0, y0), (x1, y1) = pts[0], pts[-1]
        mx, my = (x0 + x1) / 2 - loop_c[0], (y0 + y1) / 2 - loop_c[1]
        dx, dy = x1 - x0, y1 - y0
        r = math.hypot(mx, my) or 1
        tang = (dx * -my + dy * mx) / r                                  # + = clockwise on screen (y down)
        rad = (dx * mx + dy * my) / r                                    # + = away from the Loop
        flip = tang < 0 if abs(tang) > abs(rad) * .4 else rad < 0
        return (b, a, pts[::-1]) if flip else (a, b, pts)
    edges = [canon(a, b) for a, b in edges]
    out = {
        "note": "Generated by tools/build_layout.py from data/stations.json. Positions are schematic map units.",
        "size": [round(float(pos[:, 0].max()) + 40, 1), round(float(pos[:, 1].max()) + 40, 1)],
        "order": ORDER,
        "loop_center": [round(float(loop_c[0]), 1), round(float(loop_c[1]), 1)],
        "stations": [{**st[s], "x": P[s][0], "y": P[s][1],
                      "gx": round(geo[s][0], 4), "gy": round(geo[s][1], 4)} for s in ids if s in st],
        "junctions": [{"id": s, "x": P[s][0], "y": P[s][1]} for s in ids if s not in st],
        "edges": [{"a": a, "b": b, "pts": pts, "lines": [l for l in ORDER if l in edge_lines[frozenset((a, b))]]} for a, b, pts in edges],
        "routes": routes,
        "platforms": d["platforms"],
        "geo_center": CENTER,
    }
    json.dump(out, open("data/layout.json", "w"), separators=(",", ":"))
    print("wrote data/layout.json", out["size"])


if __name__ == "__main__":
    main()
