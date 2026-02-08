#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-marketsafe}"
DB_MODE="${DB_MODE:-prod}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
until mysqladmin ping -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" --silent; do
  sleep 1
done
echo "MySQL is ready."

# --- 1) Init lock table (prevents re-applying schema/seed when DB is persistent) ---
mysql -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" <<'SQL'
CREATE TABLE IF NOT EXISTS _db_init_lock (
  id INT PRIMARY KEY,
  schema_applied TINYINT NOT NULL DEFAULT 0,
  seed_applied   TINYINT NOT NULL DEFAULT 0
);
INSERT IGNORE INTO _db_init_lock (id, schema_applied, seed_applied) VALUES (1, 0, 0);
SQL

SCHEMA_DONE="$(mysql -N -s -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" \
  -e "SELECT schema_applied FROM _db_init_lock WHERE id=1;")"

if [ "${SCHEMA_DONE}" != "1" ]; then
  echo "Applying schema..."
  mysql -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" < /opt/sql/schema.sql
  mysql -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" \
    -e "UPDATE _db_init_lock SET schema_applied=1 WHERE id=1;"
  echo "Schema applied."
else
  echo "Schema already applied. Skipping."
fi

if [ "${DB_MODE}" = "dev" ]; then
  SEED_DONE="$(mysql -N -s -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" \
    -e "SELECT seed_applied FROM _db_init_lock WHERE id=1;")"

  if [ "${SEED_DONE}" != "1" ]; then
    echo "DEV mode: seeding data..."
    mysql -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" < /opt/sql/seed_dev.sql
    mysql -h "${DB_HOST}" -P "${DB_PORT}" -u root -p"${MYSQL_ROOT_PASSWORD}" "${DB_NAME}" \
      -e "UPDATE _db_init_lock SET seed_applied=1 WHERE id=1;"
    echo "Seed applied."
  else
    echo "Seed already applied. Skipping."
  fi
else
  echo "Prod mode: skipping seed."
fi

# --- 2) Stub pics refresh (always reset) ---
# This expects a volume mounted at /stub_out
if [ -d "/stub_out" ]; then
  echo "Refreshing stub pictures volume..."
  rm -rf /stub_out/*
  mkdir -p /stub_out
  cp -R /opt/stub/* /stub_out/
  echo "Stub pictures refreshed."
else
  echo "No /stub_out volume mounted. Skipping stub refresh."
fi

echo "db-init done."
