#!/bin/bash
set -euo pipefail

task_script_dir="$(cd "$(dirname "$0")" && pwd)"
task_python="$task_script_dir/../.venv/bin/python"

if [ ! -x "$task_python" ]; then
    echo "Python du projet introuvable : $task_python" >&2
    echo "Créer le venv décrit dans EffectiveAreas/INSTALLATION_FR.md." >&2
    exit 1
fi

exec "$task_python" "$task_script_dir/make_preliminary_results.py" "$@"
