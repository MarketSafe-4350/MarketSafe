FROM mysql:8.4

WORKDIR /opt

# SQL
COPY ../schema.sql /opt/sql/schema.sql
COPY ../seed_dev.sql /opt/sql/seed_dev.sql

# Stub pictures (immutable source inside the init image)
COPY ../../stub /opt/stub

# Init script
COPY init.sh /opt/init.sh
RUN chmod +x /opt/init.sh

ENTRYPOINT ["/opt/init.sh"]
