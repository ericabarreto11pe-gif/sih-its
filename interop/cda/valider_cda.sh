#!/usr/bin/env bash
# Vérifie la structure d'un compte rendu CDA R2 avec le schéma officiel HL7.
# Usage : ./interop/cda/valider_cda.sh interop/cda/CR-ACC-2026-0001.xml
# Prérequis : git et xmllint (déjà présents sur macOS).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)/.schema"
if [ ! -d "$DIR" ]; then
  echo "Téléchargement du schéma CDA R2 (HL7/CDA-core-2.0)…"
  git clone --quiet --depth 1 https://github.com/HL7/CDA-core-2.0.git "$DIR"
fi
xmllint --noout --schema "$DIR/schema/normative/infrastructure/cda/CDA.xsd" "$@"
