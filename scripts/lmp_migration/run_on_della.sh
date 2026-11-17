#!/usr/bin/env bash
# Convert the legacy LMP pickles to Parquet on della (issue #1).
#
# Usage (from a checkout of this repository on della):
#   SRC=/tigerdata/PERFORM/orfeus-data-visualization/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20 \
#   DST=/tigerdata/PERFORM/orfeus-data-visualization/data/lmps_data_visualization/t7k_v0.4.0-a2_rsvf-20-parquet \
#   scripts/lmp_migration/run_on_della.sh --dry-run
#
# Then run again without --dry-run. Any other flags (--limit N, --max-output-gb X)
# are passed to migrate_lmp_pickles.py. Safe to re-run: finished days are skipped.
#
# Environment:
#   SRC       (required) directory of legacy <YYYY-MM-DD>.p.gz files; never modified
#   DST       (required) output directory for the Parquet dataset
#   VENV_DIR  virtualenv location (default: $HOME/.venvs/orfeus-lmp-migration, outside TigerData)
#   PYTHON    interpreter used to create the virtualenv (default: python3, needs >= 3.9)
set -euo pipefail

: "${SRC:?Set SRC to the directory of legacy .p.gz files}"
: "${DST:?Set DST to the Parquet output directory}"
PYTHON="${PYTHON:-python3}"
VENV_DIR="${VENV_DIR:-$HOME/.venvs/orfeus-lmp-migration}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$SRC" ]]; then
  echo "ERROR: SRC is not a directory: $SRC" >&2
  exit 2
fi
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
  echo "ERROR: $PYTHON must be Python 3.9 or newer" >&2
  exit 2
fi

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Creating virtualenv in $VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check -r "$here/requirements.txt"

exec "$VENV_DIR/bin/python" -I "$here/migrate_lmp_pickles.py" --src "$SRC" --dst "$DST" "$@"
