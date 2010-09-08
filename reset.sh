dropdb -U smart smart
createdb -U smart -O smart --encoding='utf8' smart

wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/record_rdf/clear -O /dev/null
wget --post-data='type=native&Repository+ID=record_rdf&Repository+title=Record-level+RDF+by+context&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null

wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/demographic_rdf/clear -O /dev/null
wget --post-data='type=native&Repository+ID=demographic_rdf&Repository+title=Container-level+RDF+for+demographics&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null


wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/pha_rdf/clear -O /dev/null
wget --post-data='type=native&Repository+ID=pha_rdf&Repository+title=PHA-leve+RDF+by+context&Triple+indexes=spoc%2Cposc'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null


python manage.py syncdb