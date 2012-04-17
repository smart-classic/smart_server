#!/bin/sh

RECORD_SPARQL_REPOSITORY=record_rdf

DATABASE_NAME=smart
DATABASE_USER=smart

echo Please enter the smart database password 2 times when asked...

dropdb -U $DATABASE_USER $DATABASE_NAME
createdb -U $DATABASE_USER -O $DATABASE_USER --encoding='utf8' $DATABASE_NAME

python manage.py syncdb

