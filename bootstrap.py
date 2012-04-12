print "BOOTSTRAP"
from smart.models import *
from django.conf import settings
import os, sys
import traceback
print "DONE BOOTSTRAP imports"

# Create the chrome app and a single 'localhost' development app
MachineApp.objects.create(name='chrome',
                          consumer_key=settings.CHROME_CONSUMER,
                          secret=settings.CHROME_SECRET,
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

s = os.system

if settings.TRIPLESTORE['engine'] == "sesame":
    s("""wget --post-data='context='  http://localhost:8080/openrdf-workbench/repositories/record_rdf/clear -O /dev/null""")
    s("""wget --post-data='type=native&Repository+ID='record_rdf'&Repository+title=Record-level+RDF+by+context&Triple+indexes=spoc%2Cposc%2Ccspo'  http://localhost:8080/openrdf-workbench/repositories/NONE/create -O /dev/null""")
elif settings.TRIPLESTORE['engine'] == "stardog":
    s("""stardog-admin drop -n record_rdf""")
    s("""stardog-admin create -n record_rdf -t D -u admin -p admin --server snarl://localhost:5820""")

# then add additional apps by manifest
from bootstrap_helpers import bootstrap_applications
