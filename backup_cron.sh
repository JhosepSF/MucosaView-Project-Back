#!/usr/bin/env bash
set -euo pipefail

# Configurable por variables de entorno.
DB_NAME="${DB_NAME:-mucosa_db}"
DB_USER="${DB_USER:-mucosa_user}"
DB_PASSWORD="${DB_PASSWORD:-}"
MYSQL_CNF="${MYSQL_CNF:-$HOME/.my.cnf}"
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/MucosaView-Project-Back}"
MEDIA_DIR="${MEDIA_DIR:-$PROJECT_DIR/media/photos}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/copias_seguridad}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
ZIP_NAME="backup-${TIMESTAMP}.zip"
TMP_DIR="$(mktemp -d)"
SQL_NAME="anemia.sql"

cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$BACKUP_DIR"

SQL_PATH="$TMP_DIR/$SQL_NAME"
if [ -f "$MYSQL_CNF" ]; then
    mysqldump --defaults-extra-file="$MYSQL_CNF" -u "$DB_USER" "$DB_NAME" > "$SQL_PATH"
elif [ -n "$DB_PASSWORD" ]; then
    mysqldump -u "$DB_USER" "-p$DB_PASSWORD" "$DB_NAME" > "$SQL_PATH"
else
    echo "Error: define DB_PASSWORD o crea $MYSQL_CNF con credenciales de MySQL." >&2
    exit 1
fi

if [ -d "$MEDIA_DIR" ]; then
    cp -a "$MEDIA_DIR" "$TMP_DIR/fotos"
else
    mkdir -p "$TMP_DIR/fotos"
fi

(
    cd "$TMP_DIR"
    zip -r -q "$BACKUP_DIR/$ZIP_NAME" "$SQL_NAME" "fotos"
)

find "$BACKUP_DIR" -type f -name "backup-*.zip" -mtime +"$RETENTION_DAYS" -delete

echo "Backup generado: $BACKUP_DIR/$ZIP_NAME"
