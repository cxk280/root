# Project rules — Living Software

## Keep the README current as work is done
- `README.md` is the living front door of the project. **Update it on an ongoing
  basis as work is completed** — not as a separate cleanup pass later.
- Whenever a unit of work changes what is true about the project, update the
  README in the **same change/commit**. This includes:
  - completing a milestone, phase, or ladder rung (move it from ⬜ to ✅ and add
    its result);
  - adding or removing a top-level component, script, or directory (keep the
    repository-layout and quick-start sections accurate);
  - changing how to build, run, test, or set up the project;
  - landing a result worth stating (update the Status section and link the
    relevant `results/…` file);
  - adding a safety/containment control (reflect it and link `SECURITY.md`).
- Keep the **ELI5** section honest and in sync with what the system actually
  does — if behavior changes, the plain-language description changes too.
- Before opening a PR, verify the README reflects the branch's work.

## Related docs to keep consistent
- `AUTOPOIESIS.md` — the binding charter and rung-by-rung roadmap.
- `SECURITY.md` — threat model and containment controls.
- `results/RESULTS.md`, `results/protocell/…` — per-milestone results the README
  links to.
