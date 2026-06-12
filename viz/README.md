# viz — the live visualizer

Watch the organisms live, repair, forage, and die in a browser. A Python stdlib
server runs the (contained) medium and streams one frame per window over
Server-Sent Events; a vanilla-canvas frontend renders four views.

```sh
python3 -m viz.server            # → http://127.0.0.1:8808
```

Open the URL. Tabs:

- **Arena** — one organism in its decaying arena: bytes coloured by role
  (code / membrane / data), corrupted bytes flash red and heal green, the
  execution head outlined white, an integrity heartbeat. Pick the organism
  (rock … protocell2, or the 2-head colony) and the decay law (solvent *T* or
  bit-rot λ, with the threshold annotated). It dies and is reborn on a loop.
- **Forager** — chemotaxis in a 1-D world: the drifting nutrient, the gradient,
  the forager tracking it, a fuel gauge, a position-over-time trail. Drag the
  drift slider past **v\* ≈ 1.2** to watch it lose the food and starve; toggle the
  non-sensing **sweep** control.
- **Thresholds** — the recorded T\*/λ\*/v\* survival curves, the six-point
  aliveness scorecard, the Milestone-1 C-vs-asm benchmark.
- **Overview** — the ELI5 and the rung-by-rung lineage (each rung links into the
  relevant live view).

Transport: play/pause, step, speed (top right). The "contained" badge states the
isolation mode.

## How it fits together

- `medium/world.py` — `live`, `live_colony`, `live_forage` take an opt-in
  `on_frame` callback (one dict per window). Default `None` → no behavior change.
- `viz/scenes.py` — maps a request (organism, decay law, params) to a medium run.
- `viz/server.py` — `ThreadingHTTPServer` + SSE (`GET /stream`) + controls
  (`POST /control`). Paces/pauses by blocking inside the `on_frame` it passes in.
- `viz/static/` — `index.html`, `styles.css`, `app.js` (no framework, no build).

## Containment (SECURITY.md C7)

Live streaming runs the emulator **in the server process** with the C1
instruction traps active — safe for the curated demo organisms. For untrusted or
evolved organisms, run the server inside the locked-down container:

```sh
containment/run.sh python3 -m viz.server        # add a published port in run.sh
```
