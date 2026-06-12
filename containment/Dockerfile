# C4 — the locked-down container: the hard memory/network/filesystem walls.
#
# The build installs the native toolchain; every RUN that executes organism code
# happens at *run* time under `containment/run.sh`, which adds --network none,
# a read-only root filesystem, dropped capabilities, no-new-privileges, a
# non-root user, and memory/pid/cpu caps. See SECURITY.md (R1/R2/R4).
FROM debian:bookworm-slim

# Toolchain: clang (build blobs), libunicorn (emulate), python3 (harness).
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 clang libunicorn2 libunicorn-dev libcapstone-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-root, no shell privileges beyond running the harness.
RUN useradd --create-home --uid 10001 vat
WORKDIR /work
COPY --chown=vat:vat . /work
USER vat

# Default: run the full safety + science self-test suite. Overridable.
CMD ["python3", "containment/selftest_all.py"]
