#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -d "venv" ]; then
  source venv/bin/activate
fi

log() { echo -e "\n➡️  $1\n"; }

# --- Build Text ---
log "Building Stack Sans Text..."
gftools builder sources/config-text.yaml

# --- Build Headline ---
log "Building Stack Sans Headline..."
gftools builder sources/config-headline.yaml

# --- Prepare Notch ---
log "Preparing Stack Sans Notch source..."
mkdir -p sources/generated

python3 scripts/prepare_notch.py \
  sources/StackSansHeadline.glyphspackage \
  sources/generated/StackSansNotch.glyphspackage

# --- Vérifie que le fichier a bien été créé ---
if [ ! -d "sources/generated/StackSansNotch.glyphspackage" ]; then
  echo "❌ StackSansNotch.glyphspackage n'a pas été généré — build annulé."
  exit 1
fi

# --- Build Notch ---
log "Building Stack Sans Notch..."
gftools builder sources/config-notch.yaml

log "✅ All builds complete!"
