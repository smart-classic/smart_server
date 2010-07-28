dropdb -U smart redland
dropdb -U smart smart
createdb -U smart -O smart --encoding='utf8' smart
createdb -U smart -O smart --encoding='utf8' redland
python manage.py syncdb

PG_PATH="/usr/bin"
CS_DATA_LOC="codingsystems/data"
DBNAME="smart"
if [[ -e ${CS_DATA_LOC}/load-snomedctcore.sql ]]
then
    $PG_PATH/psql -U smart -f ${CS_DATA_LOC}/load-snomedctcore.sql $DBNAME
fi
