#!/usr/bin/env bash
# C4 — run the rig inside the locked-down container with hard walls.
#
# These flags are the containment guarantees the host OS could only
# best-effort (SECURITY.md R1/R2/R4):
#   --network none            no network egress at all
#   --read-only               root filesystem is immutable...
#   --tmpfs /work/.scratch    ...except an explicit, ephemeral scratch space
#   --cap-drop ALL            no Linux capabilities
#   --security-opt no-new-privileges  cannot regain privilege
#   --pids-limit / --memory / --cpus  bounded processes, RAM, CPU
#   --user 10001              non-root
#
# Usage: containment/run.sh [command...]   (default: the full self-test suite)
set -euo pipefail
IMAGE="${IMAGE:-living-software:contained}"
cd "$(dirname "$0")/.."

docker build -t "$IMAGE" -f containment/Dockerfile .

exec docker run --rm \
    --network none \
    --read-only \
    --tmpfs /work/.scratch:rw,noexec,nosuid,size=256m \
    --tmpfs /tmp:rw,noexec,nosuid,size=64m \
    --cap-drop ALL \
    --security-opt no-new-privileges \
    --pids-limit 256 \
    --memory 2g \
    --cpus 2 \
    --user 10001 \
    -e TMPDIR=/work/.scratch \
    "$IMAGE" "$@"
