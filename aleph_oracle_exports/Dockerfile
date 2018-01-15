FROM mariadb

ENV REFRESHED_AT 2018-01-15
ENV MAINTAINER Deutsches Archäologisches Institut "dev@dainst.de"

ENV MYSQL_ROOT_PASSWORD root
ENV MYSQL_DATABASE_NAME koha_mapping_db
ENV MYSQL_USER_NAME koha_zenon
ENV MYSQL_USER_PASSWORD zenon

RUN echo "Creating Koha-DB-User ..."
RUN echo "CREATE database if not exists $MYSQL_DATABASE_NAME; \
        GRANT ALL ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_USER_NAME'@'localhost' IDENTIFIED BY '$MYSQL_USER_PASSWORD' WITH GRANT OPTION ; \
        GRANT ALL ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_USER_NAME'@'%' IDENTIFIED BY '$MYSQL_USER_PASSWORD' WITH GRANT OPTION ; \
        FLUSH PRIVILEGES ;" > /docker-entrypoint-initdb.d/00_create_db_and_user.sql

COPY mariadb_table_setup/currency_create_and_fill.sql /docker-entrypoint-initdb.d/01_currency_create_and_fill.sql
COPY mariadb_table_setup/aqbooksellers_create.sql /docker-entrypoint-initdb.d/02_aqbooksellers_create.sql
COPY mariadb_table_setup/aqcontacts_create.sql /docker-entrypoint-initdb.d/03_aqcontacts_create.sql

EXPOSE 3306