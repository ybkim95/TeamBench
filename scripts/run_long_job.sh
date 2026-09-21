#!/bin/bash
# Preflight a long job, then keep its Kerberos ticket alive while it runs.
#
# Why this exists
# ---------------
# The repository is on an NFS mount with sec=krb5p, so every file write needs a
# live Kerberos ticket. Tickets here last two days. Once one lapses it cannot be
# renewed even though the renewable window is ten days: "kinit -R" answers
# "Ticket expired while renewing credentials". And the kernel caches a GSS
# context for a while past expiry, so a job writes happily for an hour or two
# and only then starts failing.
#
# That is how a 288-run sweep died after 6 runs, with OSError Errno 127 out of a
# checkpoint append. The run-level fix is in harness/ablation.py::durable_append,
# which keeps a completed run rather than losing it. This is the other half:
# refuse to start a multi-day job on a ticket that will not survive it, and renew
# the ticket periodically so it never lapses in the first place.
#
# Usage:
#   scripts/run_long_job.sh --hours 50 -- .venv/bin/python -u scripts/run_budget_sweep.py ...
set -u

HOURS=24
NEED_GB=12
while [ $# -gt 0 ]; do
  case "$1" in
    --hours) HOURS="$2"; shift 2 ;;
    --need-gb) NEED_GB="$2"; shift 2 ;;
    --) shift; break ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ $# -gt 0 ] || { echo "nothing to run; pass the command after --" >&2; exit 2; }

fail() { echo "[preflight] FAIL: $*" >&2; exit 1; }

# 1. A ticket must exist and outlive the job, or be renewable past it.
klist -s 2>/dev/null || fail "no valid Kerberos ticket. Run: kinit"

need_epoch=$(( $(date +%s) + HOURS * 3600 ))
renew_line=$(klist 2>/dev/null | grep -o 'renew until.*' | head -1 | sed 's/renew until *//')
if [ -n "$renew_line" ]; then
  renew_epoch=$(date -d "$renew_line" +%s 2>/dev/null || echo 0)
  if [ "$renew_epoch" -lt "$need_epoch" ]; then
    fail "ticket is renewable only until $renew_line, which is short of the ${HOURS}h this job needs. Run: kinit"
  fi
  echo "[preflight] ticket renewable until $renew_line, past the ${HOURS}h needed"
else
  fail "ticket is not renewable, so it cannot survive a ${HOURS}h job. Run: kinit -r 7d"
fi

# 2. Local disk, where run directories and the checkpoint fallback live.
avail_gb=$(df -BG --output=avail /tmp | tail -1 | tr -dc '0-9')
[ "${avail_gb:-0}" -ge "$NEED_GB" ] || \
  fail "only ${avail_gb}G free on /tmp, need ${NEED_GB}G. Check: du -sh /tmp/* | sort -h | tail"
echo "[preflight] /tmp has ${avail_gb}G free, need ${NEED_GB}G"

# 3. Survive logout.
if command -v loginctl >/dev/null 2>&1; then
  loginctl show-user "$USER" 2>/dev/null | grep -q 'Linger=yes' \
    && echo "[preflight] systemd linger on" \
    || echo "[preflight] WARNING: linger off; nohup'd jobs may die at logout (sudo loginctl enable-linger $USER)"
fi

# 4. Run under krenew so the ticket is refreshed before it can lapse.
#    -K 60: wake every 60s.  -b: background.  -t: would run aklog, which this
#    host does not have, so it is omitted deliberately.
if command -v krenew >/dev/null 2>&1; then
  echo "[preflight] launching under krenew (renewing every 60s)"
  exec krenew -K 60 -- "$@"
fi
echo "[preflight] WARNING: krenew absent; ticket will not be renewed"
exec "$@"
