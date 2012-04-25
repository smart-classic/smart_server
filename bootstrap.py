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

endpoint = settings.TRIPLESTORE['record_endpoint']
repo = endpoint.split("/")[-1]
base_url = endpoint.replace(repo, "")

if settings.TRIPLESTORE['engine'] == "sesame":
    s("""wget --post-data='context='  %s/clear -O /dev/null""" % endpoint)
    s("""wget --post-data='type=native&Repository+ID='%s'&Repository+title=Record-level+RDF+by+context&Triple+indexes=spoc\%2Cposc\%2Ccspo'  %sNONE/create -O /dev/null""" % (repo, base_url))
elif settings.TRIPLESTORE['engine'] == "stardog":
    s("""stardog-admin drop -n %s""" % repo)
    s("""stardog-admin create -n %s -t D -u admin -p admin --server snarl://localhost:5820""" % repo)

# then add additional apps by manifest
from bootstrap_helpers import bootstrap_applications
