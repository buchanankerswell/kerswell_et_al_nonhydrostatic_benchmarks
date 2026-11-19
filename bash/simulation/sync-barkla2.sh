#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../utils/log.sh"

if [ $# -ne 3 ]; then
  log_warn "Usage: $0 <TIMESTEPS> <LOCAL_SIM_DIR> <REMOTE_SIM_DIR>"
  exit 1
fi

read -r -a MODEL_TIMESTEPS <<<"$1"
LOCAL_SIM_DIR="$2"
REMOTE_SIM_DIR="$3"

REMOTE_USER="kersweb"
REMOTE_HOST="barklaviz2.liv.ac.uk"

CONTROL_SOCKET="$HOME/.ssh/cm_socket_%h_%p_%r"
SSH_BASE=(ssh -o ControlMaster=auto -o ControlPersist=15m -o ControlPath="$CONTROL_SOCKET")
RSYNC_OPTS=(-az --out-format='%f' -e "${SSH_BASE[*]}")

log_info "Establishing SSH multiplexed connection"
"${SSH_BASE[@]}" -MNf "${REMOTE_USER}@${REMOTE_HOST}" 2>&1 | log_pipe

log_info "Syncing .run files"
mkdir -p "$LOCAL_SIM_DIR/configs"
rsync "${RSYNC_OPTS[@]}" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_SIM_DIR}/configs/*.run" "$LOCAL_SIM_DIR/configs/" 2>/dev/null | log_pipe || true

FILTERS=(--exclude="restart/" --exclude="checkpoint-*/" --include="*/")
for tstep in "${MODEL_TIMESTEPS[@]}"; do
  padded="$(printf '%05d' "$((10#$tstep))")"
  FILTERS+=(--include="solution-${padded}.pvtu" --include="solution-${padded}.*.vtu")
done
FILTERS+=(--include="statistics" --include="point_values.txt" --include="*.log" --exclude="*")

log_info "Syncing results"
mkdir -p "$LOCAL_SIM_DIR/results"
rsync "${RSYNC_OPTS[@]}" "${FILTERS[@]}" \
  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_SIM_DIR}/results/" "$LOCAL_SIM_DIR/results/" 2>/dev/null | log_pipe || true

log_info "Sync complete"
