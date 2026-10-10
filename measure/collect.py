"""Samples CTABot's Worker (/cta/positions) every 15 s for 20 minutes and saves every answer, to measure how
accurate and how fresh CTA's train positions are. Temporary: lives only on the 'measure' branch."""
import gzip, json, sys, time, urllib.request

URL = "https://transit-aquarium.edawk10.workers.dev/cta/positions"
EVERY, FOR = 15, 20 * 60
out = []
t_end = time.time() + FOR
while time.time() < t_end:
    t0 = time.time()
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "ctabot feed check (+https://github.com/evan-dawkins/ctabot)"})
        body = json.load(urllib.request.urlopen(req, timeout=20))
        out.append({"asked": int(t0 * 1000), "took_ms": int((time.time() - t0) * 1000), "data": body})
        print(f"{time.strftime('%H:%M:%S')} {body.get('trains')} trains", flush=True)
    except Exception as e:
        out.append({"asked": int(t0 * 1000), "error": str(e)})
        print("error:", e, file=sys.stderr, flush=True)
    time.sleep(max(0, EVERY - (time.time() - t0)))
name = "measure/" + time.strftime("%Y-%m-%d-%H%M", time.localtime()) + "-samples.json.gz"
with gzip.open(name, "wt") as f:
    json.dump(out, f, separators=(",", ":"))
print("saved", name, len(out), "samples")
