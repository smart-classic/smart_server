dropdb -U smart redland
dropdb -U smart smart
createdb -U smart -O smart --encoding='utf8' smart
createdb -U smart -O smart --encoding='utf8' redland
python manage.py syncdb
