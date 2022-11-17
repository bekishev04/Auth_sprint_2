FROM postgres:13-bullseye

RUN apt-get update && apt-get -y install postgresql-13-cron git build-essential postgresql-server-dev-13
RUN git clone https://github.com/pgpartman/pg_partman.git
RUN cd pg_partman && make && make install
RUN cd .. && \
    rm -rf pg_partman && \
    apt-get remove -y git build-essential postgresql-server-dev-13 && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    apt-get purge

COPY init-db /docker-entrypoint-initdb.d
