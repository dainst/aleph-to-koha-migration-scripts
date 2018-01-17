# Oracle export scripts

Each Python file is named after the Koha database table it is supposed to produce data for. This data is read from
different Aleph Oracle tables.

## Folders

* `mappings` contains utility scripts used by the main Python scripts.
* `mariadb_table_setup` contains SQL files used to populate the empty mapping mariadb. The mapping database mirrors
tables used by Koha, but adds additional columns for storing Aleph keys. This is necessary to map from old Aleph keys to
new Koha Keys.
* `mariadb_intermediate_values` contains SQL files that are used to automatically insert intermediate results into the
mapping database when running `docker-compose build`.
* `ready_for_import` contains the final results, that can be imported into a running Koha instance.

## Koha insertion order

You can find a recommended data insertion order for Koha [online](http://schema.koha-community.org/17_05/insertionOrder.txt).