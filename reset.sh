#!/bin/sh

RECORD_SPARQL_REPOSITORY=record_rdf
TEMP_SPARQL_REPOSITORY=temp_rdf
PHA_SPARQL_REPOSITORY=pha_rdf

DATABASE_NAME=smart
DATABASE_USER=smart

echo Please enter the smart database password 3 times when asked...

dropdb -U $DATABASE_USER $DATABASE_NAME
createdb -U $DATABASE_USER -O $DATABASE_USER --encoding='utf8' $DATABASE_NAME

wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/$RECORD_SPARQL_REPOSITORY/clear -O /dev/null
wget --post-data='type=native&Repository+ID='$RECORD_SPARQL_REPOSITORY'&Repository+title=Record-level+RDF+by+context&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null

wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/$TEMP_SPARQL_REPOSITORY/clear -O /dev/null
wget --post-data='type=native&Repository+ID='$TEMP_SPARQL_REPOSITORY'&Repository+title=Container-level+RDF+for+temporary_storage&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null

wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/$PHA_SPARQL_REPOSITORY/clear -O /dev/null
wget --post-data='type=native&Repository+ID='$PHA_SPARQL_REPOSITORY'&Repository+title=PHA-leve+RDF+by+context&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null

python manage.py syncdb

