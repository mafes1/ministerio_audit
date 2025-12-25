#!/usr/bin/env bash
set -euo pipefail

# === Configuración ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/../..")"

MAILDIR="$PROJECT_ROOT/data/raw/maildir"
MBSYNC_LOGS="$PROJECT_ROOT/runs/mail/mbsync/logs"
MBSYNC_STATE="$PROJECT_ROOT/runs/mail/mbsync/state"
MU_HOME="$PROJECT_ROOT/runs/mail/mu"

echo "Limpieza de datos del proyecto Ministerio_CV"
echo "Esto eliminará TODO el correo descargado, índices y logs."
echo
echo "Se mantendrá la configuración:"
echo " - $PROJECT_ROOT/secrets/mbsyncrc"
echo " - $PROJECT_ROOT/secrets/passwords.txt (si existe)"
echo
read -rp "¿Seguro que quieres continuar? (yes/no): " confirm
[[ "$confirm" == "yes" ]] || { echo "Cancelado."; exit 1; }

# === Borrado seguro ===
echo "→ Eliminando maildir..."
rm -rf "$MAILDIR"

echo "→ Eliminando logs y estado de mbsync..."
rm -rf "$MBSYNC_LOGS" "$MBSYNC_STATE"

echo "→ Eliminando base de datos de mu..."
rm -rf "$MU_HOME"

# === Reconstrucción de estructura vacía ===
mkdir -p "$MAILDIR" "$MBSYNC_LOGS" "$MBSYNC_STATE"

echo "Limpieza completada."
