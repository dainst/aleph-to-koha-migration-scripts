# Setup

[Docker](https://www.docker.com/community-edition) and [docker-compose](https://docs.docker.com/compose/) are used for 
setting up (and resetting) the intermediate mapping database when exporting data from Aleph's Oracle database 
(with [oracle_exports.py](oracle_exports.py) or its library scripts).


All scripts are written and tested using Python 3. 

You may need to install some additional libraries (for example using __pip3__, see also: [requirements.txt]
(requirements.txt)):

* [pymarc](https://github.com/edsu/pymarc): used to read and write [MARC format](https://www.loc.gov/marc/) data.
* [cx_Oracle](https://oracle.github.io/python-cx_Oracle/): used to access Aleph's Oracle database. 
  * __cx_Oracle__ itself requires Oracle's [Instant Client](http://www.oracle.com/technetwork/database/features/instant-client/index.html) to be 
installed and its environment variables set. 
  * Examples: Setting the __Instant Client__ environment variable (version 12.2):
    * Fedora: `export LD_LIBRARY_PATH=/opt/oracle/instantclient_12_2:$LD_LIBRARY_PATH`
    * Ubuntu: `export LD_LIBRARY_PATH=/usr/lib/oracle/12.2/client64/lib/${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}`
* [mysqlclient](https://github.com/PyMySQL/mysqlclient-python): used to access Koha's mariadb.

## Docker cheat sheet

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
