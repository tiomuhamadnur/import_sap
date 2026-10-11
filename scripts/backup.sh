#!/bin/sh
set -eu

RETENTION="${BACKUP_RETENTION_DAYS:-14}"
INTERVAL="${BACKUP_INTERVAL_SECONDS:-86400}"

mkdir -p /backups

echo "[backup] service started (retention=${RETENTION}d, interval=${INTERVAL}s)"

while true; do
    ts="$(date +%Y%m%d_%H%M%S)"
    file="/backups/${PGDATABASE}_${ts}.dump"
    if pg_dump -Fc -f "${file}"; then
        echo "[backup] created ${file}"
    else
        echo "[backup] FAILED to create dump" >&2
    fi

    find /backups -name "${PGDATABASE}_*.dump" -type f -mtime "+${RETENTION}" -delete

    sleep "${INTERVAL}"
done
