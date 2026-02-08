FROM mysql:8.4

WORKDIR /opt

# These paths are relative to the BUILD CONTEXT: ./persistence/db
COPY schema.sql /opt/sql/schema.sql
COPY seed_dev.sql /opt/sql/seed_dev.sql

# Stub folder is NOT inside ./persistence/db, so you have 2 options:
# (A) move stub into ./persistence/db, or
# (B) change build context (see Fix 2), or
# (C) remove stub copying from db-init for now

# Copy init script (it lives under ./persistence/db/init/init.sh)
COPY init/init.sh /opt/init.sh
RUN chmod +x /opt/init.sh

ENTRYPOINT ["/opt/init.sh"]
