# Intermediate result folder

SQL data ready for import into the mapping database is put here. 

All scripts should write data to the mapping database automatically. But if the mariadb container is being rebuild, files 
residing here are used to populate tables without the need to run all export scripts again.