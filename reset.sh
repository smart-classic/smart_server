dropdb -U smart redland
dropdb -U smart smart
createdb -U smart -O smart --encoding='utf8' smart
createdb -U smart -O smart --encoding='utf8' redland
python manage.py syncdb
wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/record_rdf/clear -O /dev/null
wget --post-data='type=native&Repository+ID=record_rdf&Repository+title=Record-level+RDF+by+context&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null
