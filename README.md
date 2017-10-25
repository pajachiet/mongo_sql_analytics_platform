# Mongo SQL Analytics Platform
A Docker architecture to assemble an SQL analytics platform for MongoDB

- Are you trap in the MongoDB Analytics gap ? 
- Are you looking for an open-source solution to analyse your MongoDB data ? 

Then this project is made for you ! It can be used 'as is', or adapted to cover your specific needs. 
  
## Getting started

This architecture has been tested on Mac & Linux systems, not on Windows.

You will need a **good internet connexion** to install all Docker images.

### Prerequisites : Docker & Docker Compose

- Follow [instructions](https://docs.docker.com/engine/installation/) to install Docker Community Edition (CE) on your system. 
- Then follow [instructions](https://docs.docker.com/compose/install/) to install Docker Compose. On Mac, compose is packaged with Docker, so you can skip this step.
 
 
### Getting the project

Clone the project to a local folder

    git clone git@github.com:pajachiet/mongo_sql_analytics_platform.git
    cd mongo_sql_analytics_platform

Read **'run.sh'** usage. Latter on, you should also read the script to understand how it works.
    
    ./run.sh --help

### Run demonstration 

    ./run.sh demo
    
This will 

- Install all services
- Download demonstration data, then restore it in a MongoDB database 'demo'
- Extract the data model of MongoDB and map it to a relational model
    - Look in 'volumes/mongoconnector/data' for **schema_demo.md** and **mapping_demo.json** files
- Synchronize data from MongoDB to PostgreSQL

- Launch superset and import dashboards on demo data
    - Go to **localhost:8088**, and connect with user **admin**, password **admin**
- Extract a diagram of the relational data model
    - Look in 'volumes/sqlschema/data' for file **sql_schema_demo.pdf**

## Architecture 

### Services 

The architecture leverages Docker Compose, with the following services :
- **mongosource** : MongoDB database we want to analyze
- **mongoconnector** : Main service. It maps and synchronizes data between *mongosource* and *postgres*. See details on mongoconnector below. 
- **postgres** : Store MongoDB data, mapped to a relational model
- **superset** : Open-Source analytics web service, to demonstrate how MongoDB data can easily be analyzed once in postgres. 
- **redis** : Superset caching database
- **schemacrawler** : Create a diagram of PostgresSQL database 

<img src="doc/services_architecture.png" alt="Services Architecture" width=800  />

Its principle have been exposed in a talk at PyParis 2017 **"Open-Source Analytics On MongoDB, with Schema"** ([youtube video](https://www.youtube.com/watch?v=J5Qn4r8nTpU), [slideshare](https://fr.slideshare.net/PoleSystematicParisRegion/opensource-analytics-stack-on-mongodb-with-schema-pierrealain-jachiet-and-aurlien-gervasi))

### Details on mongoconnector service
**mongoconnector** is the main service of this platform. It leverages the following projects:
 
- **mongo-connector**, which sync data from a MongoDB database
- **mongo-connector-postgresql**, a doc-manager to use PostgreSQL as the target DB of *mongo-connector*
- **pymongo-schema**, to *extract* MongoDB data model, and *map* it to a relational model used by *mongo-connector-postgresql*


## Custom usage, with your own MongoDB data

### Install the platform

    ./run.sh install

### Read and edit variables in **'.env'** file  
  - Superset admin password and secret key to strong ones
  - Superset mapbox key, to draw maps in Superset

### option A : Using your own MongoDB data dump.

- Create a dump folder


    DB_NAME="mydb"
    mkdir -p volumes/mongosource/data/dump/${DB_NAME}

- Copy-Paste your data dump in this folder. This dump can either be a list of bson or json files.

- Restore data in mongosource


    ./run.sh restore

### option B : Connecting to an external MongoDB database

This is not possible yet, see [TODO](#TODO). 

Edit MongoDB host and port in **'.env'** file
  

### Synchronize data in PostgreSQL

#### (optional) Edit namespaces.json
**'volumes/mongoconnector/conf/namespaces.json'** file should be edited using mongo-connector syntax for [Filtering Documents per Namespace](https://github.com/mongodb-labs/mongo-connector/wiki/Configuration-Options#filtering-documents-per-namespace). See also 'volumes/mongoconnector/namespaces_examples.json'.
 
This file is used twice

 - To list MongoDB databases to analyze
    - All databases in MongoDB if namespaces is empty (Default)
    - Databases present in at least one 'db.collection' namespaces otherwise (even if value is false)

 - Filtering collections and fields to map to PostgreSQL

#### Launch synchronization
**BEWARE** : mongoconnector service delete ALL DATA in target PostgreSQL databases.  

    ./run.sh connector
    
#### Look at your MongoDB data model
 
You may be interested to take a look at the data model extracted from your MongoDB data.

Read 'volumes/mongoconnector/data/schema_**DB_NAME**.md' file.

You can also check that your schema has been correctly filtered by 'namespaces.json', by looking at 'schema_filtered_**DB_NAME**.md' file.
    
    
#### Launch and initialize Superset

    ./run.sh superset


# Contributing

If you use this architecture, please let us know.

Contributions are most welcomed to improve it. 

Github Issues and Pull-Requests will be greatly appreciated.

Please bear in mind that some issues may be related to specific projects used here.
They will find a better home in the corresponding github repositories.


## TODO

By decreasing priority order : 
 
- Publish pymongo-schema on PyPi and install it from there
- Set specific versions in requirements.txt files
- Allow to use external MongoDB & PostgreSQL databases. We will need to 
    - tweak Docker network to connect on host databases
    - remove automatic dependency of mongoconnector to mongosource and postgres in docker-compose

- Improve mongoconnector scripts quality (function are too long, documentation is too sparse)
- Improve 'volumes/mongoconnector/namespaces_examples.json'
- Add functional tests. Automate them with travis

# Limitations

## Scaling 
The main limitation of this approach is that it cannot currently scale to very large MongoDB databases. 

- pymongo-schema could be improved to only scan part of the MongoDB database
- PostgreSQL can be tuned to improve interactive analytics (good resource [here](https://fr.slideshare.net/pgconf/five-steps-perform2009,
)), up to a certain point. If one reach its limits, he could consider writing another or more general (sql alchemy compatible) doc manager, to synchronize data to a database more specialized on analytics.  
 
## Data model evolution
With this architecture, evolution of the data model in MongoDB is not automatically taken into account. One should extract again the data model, and restart synchronization from scratch. 
 
One improvement we made on a specific project is to directly extract MongoDB data model from the code of the application. This avoid to scan MongoDB data, and allows to restart synchronization just after the deployment of a new version of the application. Unfortunately this is specific to each project using MongoDB. And we will always need to restart synchronization from scratch to take into account evolutions of the data model.

# Contributors

This platform has been assembled by the following contributors
- @pajachiet
- @Webgardener
- @aureliengervasi
- @JulieRossi

# Acknowledgements

This platform assembles services from the following open-source projects. Big thanks to them !

- [mongo-connector](https://github.com/mongodb-labs/mongo-connector)
- [mongo-connector-postgresql](https://github.com/Hopwork/mongo-connector-postgresql)
- [pymongo-schema](https://github.com/pajachiet/pymongo-schema)
- [superset](https://github.com/apache/incubator-superset)