#!/usr/bin/env bash

if [[ $# -ne 3 ]]
then
    echo "Please provide as arguments:"
    echo "1) MariaDB user"
    echo "2) MariaDB user password"
    echo "3) MariaDB database name"
else
    mysql -u$1 -p$2 $3 < reset.sql
    mysql -u$1 -p$2 $3 < aqbudgetperiods_data_import.sql
    mysql -u$1 -p$2 $3 < serial_data_import.sql
    mysql -u$1 -p$2 $3 < aqbooksellers_data_import.sql
    mysql -u$1 -p$2 $3 < aqbudgets_data_import.sql
    mysql -u$1 -p$2 $3 < subscription_frequencies_data_import.sql
    mysql -u$1 -p$2 $3 < subscription_numberpatterns_data_import.sql
    mysql -u$1 -p$2 $3 < aqbasketgroups_data_import.sql
    mysql -u$1 -p$2 $3 < aqbasket_data_import.sql
    mysql -u$1 -p$2 $3 < subscription_data_import.sql
    mysql -u$1 -p$2 $3 < aqinvoices_data_import.sql
    mysql -u$1 -p$2 $3 < aqorders_data_import.sql
    mysql -u$1 -p$2 $3 < aqcontacts_data_import.sql
    mysql -u$1 -p$2 $3 < aqorders_items_data_import.sql
    mysql -u$1 -p$2 $3 < serialitems_data_import.sql
    mysql -u$1 -p$2 $3 < finalize.sql
fi


