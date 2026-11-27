#!/bin/bash
# Supprime les morceaux d'un live plus vieux que N minutes (par défaut 45) : live_clean.sh <dossier_live> [minutes]
d="$1"; m="${2:-45}"
while pgrep -f "live_record.py" >/dev/null; do
  find "$d" -name 'seg_*.mp4*' -mmin +"$m" -delete
  sleep 120
done
