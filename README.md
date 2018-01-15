# zenon-migration-scripts
A Collection of scripts used for migrating ZENON from Aleph to Koha.

## Prerequisites

All scripts are written and tested using Python 3. 

You may need to install some additional libraries (for example using __pip3__):

* [pymarc](https://github.com/edsu/pymarc): used to read and write [MARC format](https://www.loc.gov/marc/) data.
* [cx_Oracle](https://oracle.github.io/python-cx_Oracle/): used to access Aleph's Oracle database. 
  * __cx_Oracle__ itself requires Oracle's [Instant Client](http://www.oracle.com/technetwork/database/features/instant-client/index.html) to be 
installed and its environment variables set. 
  * Examples: Setting the __Instant Client__ environment variable (version 12.2):
    * Fedora: `export LD_LIBRARY_PATH=/opt/oracle/instantclient_12_2:$LD_LIBRARY_PATH`
    * Ubuntu: `export LD_LIBRARY_PATH=/usr/lib/oracle/12.2/client64/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}`
* [mysqlclient](https://github.com/PyMySQL/mysqlclient-python): used to access Koha's mariadb.

## General information

__All scripts should be run from the main folder.__ 

There are two strategies for migrating data from Aleph to Koha:

* Where possible, we try to use export functionality provided by Aleph. This is currently used for bibliographic and 
authority data (exported as MARC21). Exported data is further processed by several Python scripts.
* For a lot of data Aleph does not provide a means to export it directly. For those cases we are forced to extract the
data directly from Aleph's Oracle database. All data concerning acquisitions has to be exported this way.

## Oracle exports

The scripts for exporting Oracle data can be found in `aleph_oracle_exports`. Each Python script is named after the 
Koha database table, which it is supposed to produce data for (`aqbooksellers.py`, `aqcontact.py`, ...). 

Between the tables exist dependencies: There is an implicit order, in which the tables have to be filled with values. 
In order to be able to quickly reset the database some Docker functionality was added:

#### Docker

For further details see: 
[Docker docs](https://docs.docker.com/compose/reference/overview/#command-options-overview-and-help).

#### build services:

`docker-compose build` 

#### create & start the database container:

`docker-compose up`

#### stop container:

`CTRL-C`

or

`docker-compose stop`


#### start container:

`docker-compose start`

#### stop and remove container: 

`docker-compose down`

or

`docker-compose down -v` (`-v` to also remove the database volumes, otherwise just the container is deleted) 


### MARC exports

(Work in progress)

The scripts for processing MARC data exported from Aleph can be found in `aleph_marc_exports`.

1. Authority data exported from Aleph has to be preprocessed by the `authority_preparation` script, which removes 
obvious duplicates (authority data with the same value in field `001`) in the export, and copies Aleph's control number 
from field `001` to `035a`. The latter is necessary because Koha will replace `001` with its own internal control number 
on import.
2. Importing the prepared authority data into Koha.
3. Exporting the newly imported authority data out of Koha.
4. Preprocessing bibliographic data exported from Aleph with the `bibliography_preparation`, also including the 
authority data exported from __Koha__. The exported authority data is used to map the bibliographic data to the already 
present authority data in Koha.
5. Importing the prepared bibliographic data into Koha.
