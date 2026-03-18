#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"
DB_NAME="${DB_NAME:-marketsafe}"
DB_MODE="${DB_MODE:-prod}"

: "${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD is required}"

MYSQL_BASE_CMD="mysql -h ${DB_HOST} -P ${DB_PORT} -u root -p${MYSQL_ROOT_PASSWORD} ${DB_NAME}"
MYSQL_ADMIN_CMD="mysqladmin ping -h ${DB_HOST} -P ${DB_PORT} -u root -p${MYSQL_ROOT_PASSWORD} --silent"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
until sh -c "${MYSQL_ADMIN_CMD}"; do
  sleep 1
done
echo "MySQL is ready."

echo "Ensuring init lock table exists..."
sh -c "${MYSQL_BASE_CMD}" <<'SQL'
CREATE TABLE IF NOT EXISTS _db_init_lock (
  id INT PRIMARY KEY,
  schema_applied TINYINT NOT NULL DEFAULT 0,
  seed_applied TINYINT NOT NULL DEFAULT 0
);
INSERT IGNORE INTO _db_init_lock (id, schema_applied, seed_applied)
VALUES (1, 0, 0);
SQL

SCHEMA_DONE="$(sh -c "${MYSQL_BASE_CMD} -N -s -e 'SELECT schema_applied FROM _db_init_lock WHERE id=1;'")"

if [ "${SCHEMA_DONE}" != "1" ]; then
  echo "Applying schema..."
  sh -c "${MYSQL_BASE_CMD}" < /opt/sql/schema.sql
  sh -c "${MYSQL_BASE_CMD} -e 'UPDATE _db_init_lock SET schema_applied=1 WHERE id=1;'"
  echo "Schema applied."
else
  echo "Schema already applied. Skipping."
fi

if [ "${DB_MODE}" = "dev" ]; then
  SEED_DONE="$(sh -c "${MYSQL_BASE_CMD} -N -s -e 'SELECT seed_applied FROM _db_init_lock WHERE id=1;'")"

  if [ "${SEED_DONE}" != "1" ]; then
    echo "DEV mode: seeding data..."
    sh -c "${MYSQL_BASE_CMD}" < /opt/sql/seed_dev.sql
    sh -c "${MYSQL_BASE_CMD} -e 'UPDATE _db_init_lock SET seed_applied=1 WHERE id=1;'"
    echo "Seed applied."
  else
    echo "Seed already applied. Skipping."
  fi
else
  echo "Prod mode: skipping seed."
fi

if [ -d "/stub_out" ]; then
  echo "Refreshing stub pictures volume..."
  mkdir -p /stub_out
  rm -rf /stub_out/*
  cp -R /opt/stub/. /stub_out/
  echo "Stub pictures refreshed."
else
  echo "No /stub_out volume mounted. Skipping stub refresh."
fi

echo "db-init done."