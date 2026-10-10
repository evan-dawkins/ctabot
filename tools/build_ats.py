"""Downloads O'Hare's Airport Transit System (the people mover) from OpenStreetMap: the guideway and its stations.

Saves the raw OpenStreetMap answer for the airport area to data/ats_osm.json. tools/build_layout.py picks the ATS
out of it and puts it on the map. The guideway rarely changes, so this runs only when this file changes, or by hand.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import json, sys, time, urllib.parse, urllib.request

BBOX = (41.965, -87.935, 42.005, -87.855)        # south, west, north, east: O'Hare and the Multi-Modal Facility
Q = """[out:json][timeout:90];
(
  relation["route"](%s);
  way["railway"](%s);
  node["railway"](%s);
  node["public_transport"](%s);
  node["station"](%s);
);
out body; >; out skel qt;""" % ((",".join(map(str, BBOX)),) * 5)
SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
           "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]


def main():
    err = None
    for url in SERVERS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": Q}).encode(),
                                             headers={"User-Agent": "ctabot map builder (+https://github.com/evan-dawkins/ctabot)"})
                d = json.load(urllib.request.urlopen(req, timeout=120))
                els = d.get("elements") or []
                if not any(e["type"] == "way" for e in els):
                    raise ValueError("no railway ways in the answer")
                json.dump({"note": "OpenStreetMap data (c) OpenStreetMap contributors, ODbL. Saved by tools/build_ats.py.",
                           "bbox": BBOX, "elements": els}, open("data/ats_osm.json", "w"), separators=(",", ":"))
                print(f"{len(els)} elements from {url}")
                return
            except Exception as e:
                err = e
                print(f"{url}: {e}", file=sys.stderr)
                time.sleep(5)
    raise SystemExit(f"OpenStreetMap download failed: {err}")


if __name__ == "__main__":
    main()
