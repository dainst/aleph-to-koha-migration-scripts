FROM mariadb/server:10.2

ENV REFRESHED_AT 2018-02-19
LABEL maintainer="Deutsches Archäologisches Institut: dev@dainst.de"

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
        FLUSH PRIVILEGES ;" > /docker-entrypoint-initdb.d/000000_create_db_and_user.sql

COPY mariadb_table_setup/currency_create_and_fill.sql /docker-entrypoint-initdb.d/000005_currency_create_and_fill.sql
COPY mariadb_table_setup/aqbudgetperiods_create.sql /docker-entrypoint-initdb.d/000013_aqbudgetperiods_create.sql
COPY mariadb_table_setup/serial_create.sql /docker-entrypoint-initdb.d/000019_serial_create.sql
COPY mariadb_table_setup/branches_create_and_fill.sql /docker-entrypoint-initdb.d/000021_branches_create_and_fill.sql
COPY mariadb_table_setup/aqbooksellers_create.sql /docker-entrypoint-initdb.d/000023_aqbooksellers_create.sql
COPY mariadb_table_setup/aqbudgets_create.sql /docker-entrypoint-initdb.d/000024_aqbudgets_create.sql
COPY mariadb_table_setup/subscription_frequencies_create.sql /docker-entrypoint-initdb.d/000029_subscription_frequencies_create.sql
COPY mariadb_table_setup/subscription_numberpatterns_create.sql /docker-entrypoint-initdb.d/000030_subscription_numberpatterns_create.sql
COPY mariadb_table_setup/aqcontract_create.sql /docker-entrypoint-initdb.d/000033_aqcontract_create.sql
COPY mariadb_table_setup/aqbasketgroups_create.sql /docker-entrypoint-initdb.d/000034_aqbasketgroups_create.sql
COPY mariadb_table_setup/aqbasket_create.sql /docker-entrypoint-initdb.d/000038_aqbasket_create.sql
COPY mariadb_table_setup/items_create.sql /docker-entrypoint-initdb.d/000041_items_create.sql
COPY mariadb_table_setup/subscription_create.sql /docker-entrypoint-initdb.d/000043_subscription_create.sql
COPY mariadb_table_setup/subscriptionhistory_create.sql /docker-entrypoint-initdb.d/000044_subscriptionhistory_create.sql
COPY mariadb_table_setup/aqinvoices_create.sql /docker-entrypoint-initdb.d/000046_aqinvoices_create.sql
COPY mariadb_table_setup/aqorders_create.sql /docker-entrypoint-initdb.d/000050_aqorders_create.sql
COPY mariadb_table_setup/aqcontacts_create.sql /docker-entrypoint-initdb.d/000113_aqcontacts_create.sql
COPY mariadb_table_setup/aqorders_items_create.sql //docker-entrypoint-initdb.d/000117_aqorders_items_create.sql
COPY mariadb_table_setup/serialitems_create.sql /docker-entrypoint-initdb.d/000146_serialitems_create.sql

COPY mariadb_intermediate_values/* /docker-entrypoint-initdb.d/

EXPOSE 3306
