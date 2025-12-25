#!/usr/bin/env bash
# ======================================================
#  sync_mail.sh
#  Sincroniza todas las cuentas experimentales (CV04–CV15)
#  usando el archivo de configuración aislado del proyecto.
# ======================================================

set -euo pipefail

# === Rutas base ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/../..")"

CONFIG="${MBSYNC_CONFIG:-$PROJECT_ROOT/secrets/mbsyncrc}"
MAILDIR="$PROJECT_ROOT/data/raw/maildir"
LOGDIR="$PROJECT_ROOT/runs/mail/mbsync/logs"
STATE_DIR="$PROJECT_ROOT/runs/mail/mbsync/state"
TMP_CONF="$(mktemp)"

# === Cuentas a sincronizar ===
ACCOUNTS=(cv04 cv06 cv07 cv08 cv09 cv10 cv11 cv12 cv13 cv15)

# === Crear estructura base ===
mkdir -p "$MAILDIR" "$LOGDIR" "$STATE_DIR"
for acc in "${ACCOUNTS[@]}"; do
    mkdir -p "$MAILDIR/$acc/INBOX"
done

# === Archivo de log (fecha por ejecución) ===
TIMESTAMP="$(date +%Y-%m-%d_%H-%M-%S)"
LOGFILE="$LOGDIR/sync_${TIMESTAMP}.log"

echo "=== $(date -Iseconds) - sync start ===" | tee -a "$LOGFILE"

sed -e "s#data#$PROJECT_ROOT/data#g" -e "s#runs#$PROJECT_ROOT/runs#g" "$CONFIG" > "$TMP_CONF"

# === Sincronización de cada cuenta ===
for acc in "${ACCOUNTS[@]}"; do
    echo "→ Sincronizando $acc..." | tee -a "$LOGFILE"
    if mbsync -c "$TMP_CONF" "$acc" >> "$LOGFILE" 2>&1; then
        echo "$acc sincronizada correctamente." | tee -a "$LOGFILE"
    else
        echo "Error sincronizando $acc (ver $LOGFILE)" | tee -a "$LOGFILE"
    fi
done

rm "$TMP_CONF"

echo "=== $(date -Iseconds) - sync end ===" | tee -a "$LOGFILE"
echo "Sincronización completada. Log: $LOGFILE"

# === Reindexar con mu ===
if command -v mu &>/dev/null; then
    echo "→ Actualizando base de datos mu..."

    MU_HOME="$PROJECT_ROOT/runs/mail/mu"

    # Si no existe, inicializa la base
    if [ ! -d "$MU_HOME" ]; then
        echo "→ Inicializando base de datos mu en $MU_HOME..."
        mu init \
            --maildir="$MAILDIR" \
            --muhome="$MU_HOME" \
            --my-address=none
    fi

    # Indexar correos (mu >= 1.6 no necesita --maildir)
    mu index --muhome="$MU_HOME"
    echo "Base de datos mu actualizada."
else
    echo "'mu' no está instalado; omitiendo indexación."
fi
