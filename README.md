# CTABot

An unofficial live map of every CTA L train, built on the same idea as [MetraBot](https://github.com/evan-dawkins/metrabot): real positions only, never guessed.

Work in progress.

- Live data comes through a small Cloudflare Worker (shared with MetraBot, in `metrabot/worker.js`, under `/cta/`).
- Station data comes from CTA's official timetable, rebuilt weekly by a GitHub Action (`tools/build_stations.py`).

Not affiliated with the Chicago Transit Authority. Data provided by the CTA.
