FROM mariadb

ENV REFRESHED_AT 2018-01-15
ENV MAINTAINER Deutsches Archäologisches Institut "dev@dainst.de"

ENV MYSQL_ROOT_PASSWORD root
ENV MYSQL_DATABASE_NAME koha_mapping_db
ENV MYSQL_USER_NAME koha_zenon
ENV MYSQL_USER_PASSWORD zenon

RUN apt-get update
RUN apt-get install -y locales
RUN rm -rf /var/lib/apt/lists/* $
RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

RUN echo "Creating Koha-DB-User ..."
RUN echo "CREATE database if not exists $MYSQL_DATABASE_NAME; \
        GRANT ALL ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_USER_NAME'@'localhost' IDENTIFIED BY '$MYSQL_USER_PASSWORD' WITH GRANT OPTION ; \
        GRANT ALL ON $MYSQL_DATABASE_NAME.* TO '$MYSQL_USER_NAME'@'%' IDENTIFIED BY '$MYSQL_USER_PASSWORD' WITH GRANT OPTION ; \
        FLUSH PRIVILEGES ;" > /docker-entrypoint-initdb.d/00000_create_db_and_user.sql

COPY mariadb_table_setup/currency_create_and_fill.sql /docker-entrypoint-initdb.d/00001_currency_create_and_fill.sql
COPY mariadb_table_setup/aqbooksellers_create.sql /docker-entrypoint-initdb.d/00002_aqbooksellers_create.sql
COPY mariadb_table_setup/aqcontacts_create.sql /docker-entrypoint-initdb.d/00003_aqcontacts_create.sql

COPY mariadb_intermediate_values/* /docker-entrypoint-initdb.d/

EXPOSE 3306