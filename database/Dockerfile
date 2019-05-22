FROM postgres

# Copy test data over
COPY data/ /docker-entrypoint-initdb.d/data/

# Run create.sql on init
ADD create.sql /docker-entrypoint-initdb.d
