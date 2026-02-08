FROM mysql:8.4

WORKDIR /opt

# Build context is ./persistence/db, so these are correct
COPY schema.sql /opt/sql/schema.sql
COPY seed_dev.sql /opt/sql/seed_dev.sql

# init script path relative to build context
COPY init/init.sh /opt/init.sh
RUN chmod +x /opt/init.sh

ENTRYPOINT ["/opt/init.sh"]
