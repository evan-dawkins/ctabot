"""Temporary (branch 'satellite' only): downloads a few USGS imagery tiles so the satellite map can be checked
offline for alignment. Not part of the site."""
import math, os, urllib.request
URL = "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
def tx(lon, z): return int((lon + 180) / 360 * 2 ** z)
def ty(lat, z): r = math.radians(lat); return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
AREAS = [((41.60, -88.00, 42.10, -87.50), [10, 11, 12]),          # whole network
         ((41.845, -87.665, 41.905, -87.600), [13, 14, 15, 16]),  # the Loop
         ((41.965, -87.925, 42.000, -87.860), [13, 14, 15])]      # O'Hare
n = 0
for (s, w, nn, e), zs in AREAS:
    for z in zs:
        for x in range(tx(w, z), tx(e, z) + 1):
            for y in range(ty(nn, z), ty(s, z) + 1):
                p = f"satcheck/tiles/{z}/{y}/{x}.jpg"
                if os.path.exists(p): continue
                os.makedirs(os.path.dirname(p), exist_ok=True)
                req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "ctabot satellite check"})
                open(p, "wb").write(urllib.request.urlopen(req, timeout=30).read()); n += 1
print(n, "tiles")
