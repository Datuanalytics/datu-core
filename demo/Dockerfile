FROM postgres:latest



COPY data/ /csvs/

COPY init-scripts/load_csvs.sh /load_csvs.sh
RUN chmod +x /load_csvs.sh
COPY azure-init-scripts/init.sh /docker-entrypoint-initdb.d/
RUN chmod +x /docker-entrypoint-initdb.d/*.sh