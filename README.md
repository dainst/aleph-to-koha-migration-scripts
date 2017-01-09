# zenon-migration-scripts
Collection of scripts used for migrating ZENON from Aleph to Koha.

## Workflow

 (Work in progress)

1. Authority data exported from Aleph has to be preprocessed by the `authority_preparation` script, which removes obvious duplicates (authority data with the same value in field `001`) in the export, and copies Aleph's control number from field `001` to `035a`. The latter is necessary because Koha will replace `001` with its own internal control number on import.
2. Importing the prepared authority data into Koha.
3. Exporting the newly imported authority data out of Koha.
4. Preprocessing bibliographic data exported from Aleph with the `bibliography_preparation`, also including the authority data exported from __Koha__. The exported authority data is used to map the bibliographic data to the already present authority data in Koha.
5. Importing the prepared bibliographic data into Koha.
