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
* [mysqlclient](https://github.com/PyMySQL/mysqlclient-python): used to access the mapping database created by Docker, which mirrors the tables found in Koha.

## Workflow

(Work in progress)

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
