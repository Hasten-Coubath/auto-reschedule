#!/usr/bin/env sh
# Auto Reschedule - inicia o app (Linux/macOS). Autor: Hasten-Coubath
cd "$(dirname "$0")" || exit 1
exec python3 app.py "$@"
