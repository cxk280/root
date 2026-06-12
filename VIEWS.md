# VIEWS.md — the Living Software visualizer

A live web visualizer for watching the organisms of this project live, repair,
forage, and die, and for understanding the thresholds that govern them. This file
verbally specifies **every view and every state** before any UI is built; mocks
are made from this and approved before UI coding begins (global project rule).

**Platform:** a single web page served by a Python stdlib server (`viz/server.py`)
that streams per-window frames over Server-Sent Events as the medium runs. No
frontend framework; `<canvas>` rendering.

**Containment (C7):** live streaming runs the emulator inside the server process
with the C1 instruction traps active. Safe for the curated demo organisms; for
untrusted/evolved organisms the server runs inside the C4 container. The page
shows a small **"contained"** badge stating which mode is active.

## Global layout & visual language

- **Shell.** A top bar (left: title "Living Software" + the contained badge;
  center: the four view tabs — **Arena · Forager · Thresholds · Overview**;
  right: a transport cluster — ⏮ step-back is absent, ⏸/▶ play-pause, ⏭ step,
  and a speed slider 0.25×–8×). Below it the active view fills the page on a dark
  background. Content is horizontally centered with symmetric margins; the canvas
  is sized from the viewport width, not a fixed origin.
- **Palette (dark theme).** Background `#0b0e14`; panels `#141925`; text `#e6e9ef`
  on dark (high contrast); muted text `#8b93a7`. Roles/states use one consistent
  legend everywhere: **code** = slate blue `#5b8def`, **membrane** = gold
  `#f2c94c`, **data** = gray `#5a6373`, **dissolved/zero** = near-black `#1b2030`,
  **decay flash** = red `#ef5350`, **repair flash** = green `#66bb6a`,
  **execution head (RIP)** = white outline, **fuel** = teal `#2dd4bf`,
  **nutrient** = amber `#ffb74d`.
- **Every view shows a one-line plain-language caption** under its title so a
  newcomer knows what they are looking at.
- **States common to live views:** `loading` (spinner + "starting emulator…"),
  `running`, `paused`, `dead` (a translucent overlay naming the death cause),
  `error` (red toast with the message). A small HUD shows the current window
  index and, where relevant, the live metric (integrity / fuel / track-error).

---

## View 1 — Arena (an organism living and dying)

*Caption: "One organism, rebuilding its own body faster than the world erases it."*

The emotional core. Watch a single organism in its decaying arena.

- **The arena grid (center).** One cell per arena byte, laid out row-major in a
  rectangle (e.g. 480 bytes → 24×20). Each cell is filled by its **role** (code /
  membrane / data / dissolved) from the legend. On each window: bytes the decay
  law just hit **flash red** (a solvent-swept or bit-flipped byte) and bytes the
  organism just rewrote **flash green** (repair/turnover); flashes fade over a few
  frames. The **execution head (RIP)** is drawn as a white-outlined cell; in the
  colony scenario each head has its own outlined cell and a small index label.
- **Vital signs (right panel).** A large **integrity gauge** (0–100% of birth
  bytes intact) and a scrolling **heartbeat sparkline** plotting integrity and
  turnover over the last ~200 windows, with a vertical marker at any death. A
  numeric readout: window #, integrity %, turnover (bytes/window), and for the
  colony, heads-alive.
- **Controls (left panel).**
  - **Organism:** rock · blind · protocell0 · protocell1 · protocell2 · colony(2 heads).
  - **Decay law:** Solvent (with a **T slider**, the sweep period) or Bit-rot
    (with a **λ slider**, mean flips/window). The slider's current value relative
    to the known threshold (T\* ≈ 500, λ\*) is annotated so the user can dial
    across the edge of viability.
  - Transport (shared top bar) applies here.
- **States.**
  - *rock* dissolves within a window or two → red overlay "died: no turnover".
  - *blind* survives the solvent but the panel flags "no genuine boundary" (it is
    alive yet low-closure).
  - *protocell0/1/2* hold a steady integrity heartbeat; drop T below T\* (or raise
    λ) and watch integrity collapse → overlay distinguishing **membrane suicide**
    ("boundary lost — dissolved itself") from a **raw fault**.
  - *colony* shows two heads; corrupt one head's copy (high λ) and watch the other
    repair it — "head down → repaired by sibling".
- **Legend** is always visible (bottom strip) so colors are unambiguous.

---

## View 2 — Forager (chemotaxis in a 1-D world)

*Caption: "It must sense where the food is and steer toward it, or starve."*

The richest behavior, and the most legible to a newcomer.

- **The world strip (center).** A horizontal bar of 64 cells. The **nutrient**
  glows amber at its position; the **chemical gradient** is drawn as an amber
  falloff shading outward from the food (brighter = stronger signal). The
  organism's **position** is a teal marker beneath the strip that should sit on or
  near the food. A faint trail shows the last ~30 positions of both food and
  organism, so tracking (or losing the trail) is visible.
- **Fuel gauge (right).** A vertical **fuel bar** (teal) that ticks down every
  window (metabolic cost) and jumps up on a **harvest** (a brief amber pulse on
  the strip). A numeric readout: fuel, harvests, and **track-error** (mean
  distance to food). When fuel hits zero → "starved" overlay.
- **Controls (left).**
  - **Forager:** chemotaxis (`forager0`) or sweep control (`forager_sweep`).
  - **Drift speed slider** (0–2.0 steps/window) annotated with **v\* ≈ 1.2**; drag
    it past v\* to watch even the chemotaxis forager fall behind and starve.
- **States.** Chemotaxis below v\* keeps its marker glued to the food (track-error
  near the drift speed), fuel stable. Above v\* the marker lags, track-error
  climbs, fuel trends down, then "starved". The sweep control visibly ignores the
  gradient (sweeps left-to-right regardless of food) and starves at any speed —
  the panel notes "motion without sensing is not foraging".

---

## View 3 — Thresholds (what was learned)

*Caption: "Three sharp edges of viability: boundary upkeep, repair, and foraging."*

The scientific spine, read from recorded `results/` JSON (no live emulation).

- **The threshold family (top).** Three small survival-vs-parameter charts side by
  side, sharing a y-axis (survival fraction): **T\*** (solvent, survival vs sweep
  period), **λ\*** (bit-rot, survival vs flip rate — with protocell0 vs
  protocell1/TMR vs colony overlaid to show the lift), and **v\*** (foraging,
  chemotaxis vs sweep). Each marks its critical value with a labeled vertical line.
- **Aliveness scorecard (bottom-left).** The six-point Maturana–Varela key as a
  table: rows rock / blind / protocell0 / protocell1 / protocell2, columns the six
  criteria, cells ✓/✗, with the closure score (1/6 … 6/6) and a one-word verdict
  (dead / alive-no-boundary / autopoietic).
- **Milestone-1 benchmark (bottom-right).** The C-vs-asm result: per-kernel bars of
  dynamic instruction count (C ‑O3 vs final asm) and a compact tally (asm wins
  6/10 speed, 8/10 size; one-shot 10/10 correct), linking the falsification-rig
  result that gated the whole project.
- **States.** `loading` while JSON fetches; `running` (static); an `error` toast
  if a results file is missing, naming which.

---

## View 4 — Overview (the ladder & lineage)

*Caption: "Why a statue isn't alive, and how each death taught the next organism."*

The landing view; orients a newcomer before they open the live views.

- **ELI5 block (top).** A few short paragraphs (the README's plain-language
  framing) — statue vs. cell, the tide, the self-checking skin.
- **The ladder/lineage (center).** A vertical timeline of rungs: synthesis test →
  Rung 1 solvent (protocell0, T\*) → Rung 2 bit-rot (protocell1, λ\*) → Rung 2.5
  redundant execution (colony, division of labor) → Rung 2.7 foraging (forager0,
  v\*) → Rung 3 (planned). Each rung is a card with its organism, its threshold,
  and **the death that motivated the next rung** ("identity copy can't fix
  corruption → grow error correction"). Cards for built rungs link into the
  relevant live view with that scenario pre-selected.
- **States.** Static; the "planned" rung is visually dimmed.

---

## Non-goals (this iteration)

- No editing/authoring of organisms in the browser; scenarios are the curated set.
- No persistence/accounts; a session is ephemeral.
- No mobile-first layout; target a desktop browser (graceful, not optimized, on
  narrow widths).
