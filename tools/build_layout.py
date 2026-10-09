"""Builds the CTABot map from CTA's own data, and bakes it into index.html.

Inputs:  data/stations.json (tools/build_stations.py: CTA stations, stop patterns, real track shapes)
         data/geo.json      (tools/build_geo.py: Lake Michigan shoreline, city and town boundaries)
Output:  data/network.json, and the same data written into index.html between /*NET:BEGIN*/ and /*NET:END*/
         (so the page works on its own, like MetraBot).

How the map is drawn, so it can be checked:
 * True geography. 1 map unit = 1/30 km. Nothing is enlarged: the Loop is its real size and you zoom in to read it.
 * Every line follows CTA's real track shape between its stations.
 * Express runs (Purple Express on the Red Line's tracks, Red past Wellington/Diversey) are routed along the
   track they really use, so they draw beside the local line.
 * Shared track: where two lines' tracks leave a station together, the point where they really split is found
   from the shapes, and a junction is placed there. The shared part becomes one piece of track carrying both
   lines, so the page can draw them side by side (a bundle) at any zoom.
 * Side-by-side order follows one fixed order, oriented clockwise around the Loop, so a line keeps its place in
   the bundle all the way round.

Run: python tools/build_layout.py   (no network needed; numpy not needed)
"""
import json, math, os, re
from collections import defaultdict

K = 30.0                                         # map units per km
LAT0, LON0 = 42.25, -88.20                       # top-left corner of the data (matches tools/build_geo.py)
LAT1, LON1 = 41.50, -87.25
COSL = math.cos(math.radians(41.88))
ORDER = ["Purple", "Brown", "Orange", "Pink", "Green", "Red", "Blue", "Yellow"]   # side-by-side order on shared track
TOL = 0.9                                        # two tracks closer than this (~27 m) are the same track
MIN_SHARED = 2.0                                 # ...for at least this long (~66 m) before it counts as shared
KEYS = {"Red": ("red", "Red Line", "#C60C30", "Red"), "Blue": ("blue", "Blue Line", "#00A1DE", "Blue"),
        "Brown": ("brn", "Brown Line", "#62361B", "Brown"), "Green": ("g", "Green Line", "#009B3A", "Green"),
        "Orange": ("org", "Orange Line", "#F9461C", "Orange"), "Purple": ("p", "Purple Line", "#522398", "Purple"),
        "Pink": ("pink", "Pink Line", "#E27EA6", "Pink"), "Yellow": ("y", "Yellow Line", "#F9E300", "Yellow")}
BRANCH = {"Green": ["Ashland/63rd branch", "Cottage Grove branch"]}
TOWN_LABELS = ["Evanston", "Skokie", "Wilmette", "Lincolnwood", "Oak Park", "Forest Park", "Cicero", "Berwyn",
               "Rosemont", "Park Ridge", "Niles", "Evergreen Park", "River Forest", "Schiller Park", "Norridge",
               "Harwood Heights", "Oak Lawn", "Morton Grove", "Des Plaines", "Elmwood Park", "Stickney", "Burbank"]


def xy(lat, lon):
    return ((lon - LON0) * 111.32 * COSL * K, (LAT0 - lat) * 110.54 * K)


BOX = {"x0": 0.0, "y0": 0.0, "x1": round(xy(LAT1, LON1)[0], 1), "y1": round(xy(LAT1, LON1)[1], 1)}   # what the base map covers


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def plen(p):
    return sum(dist(p[i], p[i + 1]) for i in range(len(p) - 1))


def proj(p, q):
    """Closest point to q on polyline p: (distance, arc length along p)."""
    best, acc = (1e18, 0.0), 0.0
    for i in range(len(p) - 1):
        a, b = p[i], p[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy
        t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / l2))
        d = math.hypot(a[0] + dx * t - q[0], a[1] + dy * t - q[1])
        if d < best[0]:
            best = (d, acc + t * math.sqrt(l2))
        acc += math.sqrt(l2)
    return best


def point_at(p, s):
    acc = 0.0
    for i in range(len(p) - 1):
        l = dist(p[i], p[i + 1])
        if acc + l >= s and l > 0:
            t = (s - acc) / l
            return (p[i][0] + (p[i + 1][0] - p[i][0]) * t, p[i][1] + (p[i + 1][1] - p[i][1]) * t)
        acc += l
    return tuple(p[-1])


def cut(p, s0, s1):
    """Piece of polyline p between arc lengths s0 < s1."""
    out, acc = [point_at(p, s0)], 0.0
    for i in range(len(p) - 1):
        acc += dist(p[i], p[i + 1])
        if s0 < acc < s1:
            out.append(tuple(p[i + 1]))
    out.append(point_at(p, s1))
    return out


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (ax, ay), (bx, by) = pts[a], pts[b]
        dx, dy = bx - ax, by - ay; L = math.hypot(dx, dy)
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            d = abs(dy * (pts[i][0] - ax) - dx * (pts[i][1] - ay)) / L if L > 1e-9 else dist(pts[i], pts[a])
            if d > best:
                best, bi = d, i
        if best > eps:
            keep[bi] = True; stack += [(a, bi), (bi, b)]
    return [p for p, k in zip(pts, keep) if k]


def main():
    d = json.load(open("data/stations.json"))
    st = {s["id"]: s for s in d["stations"]}
    P = {sid: xy(s["lat"], s["lon"]) for sid, s in st.items()}

    # ---- 1. track between each pair of neighbouring stations, cut from CTA's real shapes
    geom = {}                                                  # frozenset(a,b) -> (a, b, pts from a to b)
    direct = defaultdict(set)                                  # frozenset(a,b) -> lines stopping at both, back to back
    for line, pats in d["lines"].items():
        for p in sorted(pats, key=lambda q: -q["trips"]):
            seq = p["stations"]
            shape = [xy(a, b) for a, b in p["shape"]]
            pos, last = [], 0.0
            for sid in seq:                                     # where each stop sits along the shape (always moving forward)
                if len(shape) < 2:
                    pos.append(None); continue
                cands = []; acc = 0.0
                for i in range(len(shape) - 1):
                    a, b = shape[i], shape[i + 1]; l = dist(a, b)
                    if acc + l < last - 1e-6:
                        acc += l; continue
                    dx, dy = b[0] - a[0], b[1] - a[1]
                    t = 0.0 if l == 0 else max(0.0, min(1.0, ((P[sid][0] - a[0]) * dx + (P[sid][1] - a[1]) * dy) / (l * l)))
                    s = max(last, acc + t * l)
                    cands.append((dist(point_at(shape, s), P[sid]), s))
                    acc += l
                # a route can pass the same spot twice (in, and back out): take the FIRST place it really reaches the stop
                best = None
                if cands:
                    m = min(c[0] for c in cands)
                    best = min((c for c in cands if c[0] <= m + 0.6), key=lambda c: c[1])
                pos.append(best[1] if best and best[0] < 4.0 else None)   # >130 m off the shape: don't trust the shape here
                if best and best[0] < 4.0:
                    last = best[1]
            for i in range(len(seq) - 1):
                a, b = seq[i], seq[i + 1]
                if a == b:
                    continue
                key = frozenset((a, b)); direct[key].add(line)
                if key in geom:
                    continue
                if pos[i] is not None and pos[i + 1] is not None and pos[i + 1] > pos[i] + 0.3:
                    g = [P[a]] + cut(shape, pos[i], pos[i + 1])[1:-1] + [P[b]]   # ends snapped exactly onto the stations
                else:
                    g = [P[a], P[b]]
                geom[key] = (a, b, g)

    graph = defaultdict(set)
    for k in geom:
        a, b = tuple(k); graph[a].add(b); graph[b].add(a)

    def via_path(a, b):
        """An express hop: a route through other stations almost as short as the direct one, on real track."""
        best, direct_len = None, dist(P[a], P[b])
        stack = [(a, [a], 0.0)]
        while stack:
            u, path, L = stack.pop()
            if L > direct_len * 1.2 or len(path) > 14:
                continue
            for v in graph[u]:
                if v in path or (u == a and v == b):
                    continue
                L2 = L + dist(P[u], P[v])
                if v == b:
                    if len(path) >= 2 and L2 <= direct_len * 1.2 and (best is None or L2 < best[1]):
                        best = (path + [b], L2)
                    continue
                stack.append((v, path + [v], L2))
        return best and best[0]

    # ---- 2. each line's routes: loop lines run out to the Loop and once around it (cut where a station repeats)
    routes = {}
    for line, pats in d["lines"].items():
        rs = []
        for p in pats:
            seq = p["stations"]
            for i, sid in enumerate(seq):
                if sid in seq[:i]:
                    seq = seq[:i + 1]; break
            drawn = [seq[0]]
            for a, b in zip(seq, seq[1:]):
                others = direct[frozenset((a, b))] - {line}
                path = None if others else via_path(a, b)
                drawn += path[1:] if path else [b]
            rs.append({"stops": seq, "drawn": drawn})
        routes[line] = rs

    # ---- 3. pieces of track: start one per neighbouring pair, then split shared stretches at real junctions
    E = {}                                                       # id -> {"a","b","pts","lines"}
    nid = [0]
    def new_edge(a, b, pts, lines):
        nid[0] += 1; E[nid[0]] = {"a": a, "b": b, "pts": [tuple(q) for q in pts], "lines": set(lines)}; return nid[0]
    chain = {}                                                   # frozenset(a,b) -> list of edge ids from a toward b (with a's id)
    pos_of = dict(P)
    for line, rs in routes.items():
        for r in rs:
            for a, b in zip(r["drawn"], r["drawn"][1:]):
                k = frozenset((a, b))
                if k not in chain:
                    ga, gb, g = geom[k]
                    chain[k] = (ga, [new_edge(ga, gb, g, [])])
                E[chain[k][1][0]]["lines"].add(line)
    # chains stay valid while edges are split: each original hop maps to the ordered edge ids that make it up
    def replace_in_chains(eid, a_side, parts):
        """Edge eid (from node a_side) was split into parts (ids, in order from a_side)."""
        for k, (start, ids) in chain.items():
            if eid in ids:
                i = ids.index(eid)
                # walk the chain to know which end of eid comes first
                node = start
                for j in range(i):
                    e = E[ids[j]]; node = e["b"] if e["a"] == node else e["a"]
                seq = parts if node == a_side else list(reversed(parts))
                chain[k] = (start, ids[:i] + seq + ids[i + 1:])

    def oriented(eid, frm):
        e = E[eid]
        return e["pts"] if e["a"] == frm else e["pts"][::-1]

    def shared_len(p1, p2):
        """How far p1 and p2 (both starting at the same node) run along the same track."""
        L1, s, step = plen(p1), 0.0, 0.3
        while s <= L1:
            q = point_at(p1, s)
            if proj(p2, q)[0] > TOL:
                return max(0.0, s - step)
            s += step
        return L1

    jn = [0]
    for _ in range(60):
        changed = False
        inc = defaultdict(list)
        for eid, e in E.items():
            inc[e["a"]].append(eid); inc[e["b"]].append(eid)
        for X in list(inc):
            ids = inc[X]
            for i in range(len(ids)):
                for j in range(len(ids)):
                    if i == j or changed:
                        continue
                    e1, e2 = ids[i], ids[j]
                    if e1 not in E or e2 not in E:
                        continue
                    p1, p2 = oriented(e1, X), oriented(e2, X)
                    far1 = E[e1]["b"] if E[e1]["a"] == X else E[e1]["a"]
                    far2 = E[e2]["b"] if E[e2]["a"] == X else E[e2]["a"]
                    if far1 == far2:
                        if shared_len(p1, p2) >= plen(p1) - 0.5:          # the same track twice: merge
                            E[e1]["lines"] |= E[e2]["lines"]
                            for k, (start, cids) in chain.items():
                                if e2 in cids:
                                    chain[k] = (start, [e1 if c == e2 else c for c in cids])
                            del E[e2]; changed = True
                        continue
                    L1, L2 = plen(p1), plen(p2)
                    s = shared_len(p1, p2)
                    if s < MIN_SHARED:
                        continue
                    if s >= L1 - 0.6:
                        # all of e1 lies along e2. Only a junction may sit mid-track; a station there would be one
                        # this line passes without stopping, which the express routing already handles.
                        if not str(far1).startswith("J") or s >= L2 - 0.6:
                            if str(far1).startswith("J") and str(far2).startswith("J") and dist(pos_of[far1], pos_of[far2]) < 1.5:
                                # two junctions found from different sides at the same spot: make them one
                                for eid, e in E.items():
                                    if e["a"] == far2: e["a"] = far1; e["pts"][0] = pos_of[far1]
                                    if e["b"] == far2: e["b"] = far1; e["pts"][-1] = pos_of[far1]
                                changed = True
                            continue
                        s2 = proj(p2, pos_of[far1])[1]
                        if s2 < 0.6 or s2 > L2 - 0.6:
                            continue
                        J = far1
                        other2 = far2
                        a2 = cut(p2, 0, s2); b2 = cut(p2, s2, L2)
                        a2[-1] = pos_of[J]; b2[0] = pos_of[J]
                        n1 = new_edge(X, J, a2, E[e2]["lines"]); n2 = new_edge(J, other2, b2, E[e2]["lines"])
                        replace_in_chains(e2, X, [n1, n2]); del E[e2]; changed = True
                        continue
                    if s >= L2 - 0.6:
                        continue                                        # handled when the pair is seen the other way round
                    # a real split: new junction where they part
                    jn[0] += 1; J = f"J{jn[0]}"
                    q = point_at(p1, s); pos_of[J] = q
                    s2 = proj(p2, q)[1]
                    a1, b1 = cut(p1, 0, s), cut(p1, s, L1)
                    a2, b2 = cut(p2, 0, s2), cut(p2, s2, L2)
                    a1[-1] = b1[0] = a2[-1] = b2[0] = q
                    shared = new_edge(X, J, a1, E[e1]["lines"] | E[e2]["lines"])
                    r1 = new_edge(J, far1, b1, E[e1]["lines"]); r2 = new_edge(J, far2, b2, E[e2]["lines"])
                    replace_in_chains(e1, X, [shared, r1]); replace_in_chains(e2, X, [shared, r2])
                    del E[e1], E[e2]; changed = True
            if changed:
                break
        if not changed:
            break
    # lines on each piece of track: recompute from the chains (merges may have moved them)
    for e in E.values():
        e["lines"] = set()
    for line, rs in routes.items():
        for r in rs:
            for a, b in zip(r["drawn"], r["drawn"][1:]):
                for eid in chain[frozenset((a, b))][1]:
                    E[eid]["lines"].add(line)
    for e in E.values():
        e["pts"] = rdp(e["pts"], 0.12)                          # ~4 m: drops points that add nothing

    # ---- 4. which side of a bundle each line takes: one order, oriented clockwise round the Loop
    lc = (P[next(s for s in st if st[s]["name"] == "Clark/Lake")][0] + 7, P[next(s for s in st if st[s]["name"] == "Clark/Lake")][1] + 13)
    def edge_flip(e):
        (x0, y0), (x1, y1) = e["pts"][0], e["pts"][-1]
        mx, my = (x0 + x1) / 2 - lc[0], (y0 + y1) / 2 - lc[1]
        dx, dy = x1 - x0, y1 - y0
        r = math.hypot(mx, my) or 1
        tang, rad = (dx * -my + dy * mx) / r, (dx * mx + dy * my) / r
        return tang < 0 if abs(tang) > abs(rad) * .4 else rad < 0     # stored direction: clockwise, or outward

    # ---- 5. output: each line's routes as one centre line with a side-by-side slot per piece
    lines_out, used = {}, set()
    for line in ORDER:
        key, name, color, api = KEYS[line]
        out_routes = []
        for ri, r in enumerate(routes[line]):
            anc, slot, ds = [], [], []
            stops = set(r["stops"])
            drawn = r["drawn"]
            node = drawn[0]
            anc.append(pos_of[node])
            ds.append(0.0)
            acc = 0.0
            for a, b in zip(drawn, drawn[1:]):
                start, ids = chain[frozenset((a, b))]
                cur = a
                seqids = ids if start == a else list(reversed(ids))
                for eid in seqids:
                    e = E[eid]
                    pts = e["pts"] if e["a"] == cur else e["pts"][::-1]
                    fwd_canon = (e["a"] == cur) != edge_flip(e)
                    ls = [l for l in ORDER if l in e["lines"]]
                    o = ls.index(line) - (len(ls) - 1) / 2
                    for q in pts[1:]:
                        acc += dist(anc[-1], q); anc.append(q); slot.append(round(o if fwd_canon else -o, 2))
                    cur = e["b"] if e["a"] == cur else e["a"]
                if b in stops:
                    ds.append(acc)
            ds_out = [round(x, 2) for x in ds]
            if len(ds_out) != len(r["stops"]):
                raise SystemExit(f"{line}: stop count mismatch ({len(ds_out)} vs {len(r['stops'])})")
            used.update(r["stops"])
            out_routes.append({"st": r["stops"], "anc": [[round(x, 2), round(y, 2)] for x, y in anc], "ds": ds_out, "slot": slot,
                               "branch": (BRANCH.get(line) or ["", ""])[ri] if len(routes[line]) > 1 else ""})
        lines_out[key] = {"code": line, "name": name, "color": color, "api": api, "routes": out_routes}

    xs = [P[s][0] for s in used]; ys = [P[s][1] for s in used]; M = 2.5 * K
    WORLD = {"x0": round(min(xs) - M, 1), "y0": round(min(ys) - M, 1), "x1": round(max(xs) + M, 1), "y1": round(max(ys) + M, 1)}
    stations = {sid: {"name": st[sid]["name"], "lat": st[sid]["lat"], "lon": st[sid]["lon"], "ada": st[sid].get("accessible", False)}
                for sid in sorted(used)}

    # ---- 6. base map: lake, towns, Chicago's street grid
    geo = json.load(open("data/geo.json"))
    ring = lambda r, eps: [[round(x, 1), round(y, 1)] for x, y in rdp([xy(a, b) for a, b in r], eps)]
    lake = [ring(r, .25) for r in geo["lake"]]
    towns = []
    for pl in geo["places"]:
        rings = [x for x in (ring(r, .5) for r in pl["rings"]) if len(x) >= 4]
        if not rings:
            continue
        big = max(rings, key=lambda r: abs(sum(r[i][0] * r[i - 1][1] - r[i - 1][0] * r[i][1] for i in range(len(r)))))
        A = sum(big[i - 1][0] * big[i][1] - big[i][0] * big[i - 1][1] for i in range(len(big))) / 2 or 1e-9
        cx = sum((big[i - 1][0] + big[i][0]) * (big[i - 1][0] * big[i][1] - big[i][0] * big[i - 1][1]) for i in range(len(big))) / (6 * A)
        cy = sum((big[i - 1][1] + big[i][1]) * (big[i - 1][0] * big[i][1] - big[i][0] * big[i - 1][1]) for i in range(len(big))) / (6 * A)
        towns.append({"name": pl["name"], "rings": rings, "label": [round(cx, 1), round(cy, 1)] if pl["name"] in TOWN_LABELS else None,
                      "rank": TOWN_LABELS.index(pl["name"]) if pl["name"] in TOWN_LABELS else 99})
    # Chicago's address grid: 0 N/S at Madison, 0 E/W at State; 800 = one mile
    ox, oy = xy(41.88207, -87.62780)
    mile = 1.609344 * K
    grid = {"origin": [round(ox, 2), round(oy, 2)], "mile": round(mile, 3)}

    net = {"note": "Generated by tools/build_layout.py from CTA's GTFS (data/stations.json) and US Census TIGER (data/geo.json).",
           "world": WORLD, "box": BOX, "proj": {"lat0": LAT0, "lon0": LON0, "k": K, "cos": COSL},
           "lines": lines_out, "stations": stations, "platforms": d["platforms"],
           "base": {"lake": lake, "towns": towns, "grid": grid}}
    js = json.dumps(net, separators=(",", ":"))
    open("data/network.json", "w").write(js)
    if os.path.exists("index.html"):
        html = open("index.html").read()
        new, n = re.subn(r"/\*NET:BEGIN\*/.*?/\*NET:END\*/", lambda m: "/*NET:BEGIN*/const NET=" + js + ";/*NET:END*/", html, flags=re.S)
        if n == 1 and new != html:
            open("index.html", "w").write(new)
            print("index.html updated")
    shared = sum(1 for e in E.values() if len(e["lines"]) > 1)
    print(f"{len(stations)} stations, {len(E)} pieces of track ({shared} shared), {jn[0]} junctions, {len(js) // 1024} KB")
    for k, L in lines_out.items():
        print(f"  {L['code']}: " + ", ".join(f"{len(r['st'])} stops / {len(r['anc'])} pts" for r in L["routes"]))


if __name__ == "__main__":
    main()
