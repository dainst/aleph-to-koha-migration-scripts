# zenon-migration-scripts
A collection of scripts used for migrating Zenon from Aleph to Koha.

## Prerequisites

See [Setup](SETUP.md).

## General information

__All scripts should be run from the main folder.__ 

There are two aspects of migrating data from Aleph to Koha:

* Where possible, we try to use export functionality provided by Aleph. This is currently used for bibliographic and 
authority data (exported as MARC21). Exported data is further processed by several Python scripts, more details 
below.
* For a lot of data Aleph does not provide a means to export it directly. For those cases we are forced to extract the
data directly from Aleph's Oracle database. All data concerning acquisitions has to be exported this way.

## Migration steps

The basic steps are as follows:
1) Preprocess the **authority** data exported from Aleph, using [authority_preparation.py](authority_preparation.py).
2) Import the preprocessed authority data into an empty Koha instance.
3) Export the authority data from Koha.
4) Preprocess the bibliographic data exported from Aleph (requires the authority data from step 3), using 
[bibliography_preparation.py](bibliography_preparation.py).
5) Import the preprocessed **bibliographic** data into the same Koha instance as in step 2. 
6) Export the bibliographic data from Koha.
7) Create a mapping between Zenon-IDs and Koha `biblio` numbers (requires export produced by step 6), using 
[bibliography_id_mapping.py](bibliography_id_mapping.py).
8) Export the table `items` from Koha as SQL:
    ```
    mysqldump --user=<user> --host=localhost --password=<pw> --port=37835 --default-character-set=utf8 --single-transaction=TRUE --no-create-info=TRUE --skip-triggers "<database>" items > items.sql 
    ```
9) Run [oracle_exports.py](oracle_exports.py) (requires Aleph Oracle DB credentials, the mapping produced by step 7 and
the `items` export produced by step 8).
10) The resulting Koha tables concerning **acquisitions** can be found at [lib/ready_for_import](lib/ready_for_import), 
including a shell [script](lib/ready_for_import/import.sh) for importing them in the correct order.

## Project structure

Docker is used to quickly recreate an intermediate mapping database (MariaDB), that contains Koha tables relevant for 
acquisitions and serial management. 

The main script [oracle_exports.py](oracle_exports.py) runs a couple of different subscripts that each produce data for 
one or several Koha tables. You can run those script separately, but be aware that certain scripts rely on previous 
ones (you can not create baskets before creating booksellers, for example).

Use Docker to debug or develop scripts without being forced to re-run all preceding scripts. 

As an example, let's say you want to debug [aqbasket](lib/aqbasket.py). The preceding scripts are 
[aqbudgets_and_aqbudgetperiods](lib/aqbudgets_and_aqbudgetperiods.py), [aqbooksellers](lib/aqbooksellers.py), 
[aqcontacts](lib/aqcontacts.py) and [aqbasketgroups](lib/aqbasketgroups.py). 

1. Run the first 4 scripts in sequence.
2. The intermediate values are saved in a [subdirectory](lib/mariadb_intermediate_values).
3. Rebuild the database **image**.
4. The intermediate values are now baked into the Docker image.
5. Delete the old **container** und start a new one.
6. Debug.
7. Repeat steps 5 and 6 until finished.