print "BOOTSTRAP"
from smart.models import *
from django.conf import settings
import os, sys
import traceback
print "DONE BOOTSTRAP imports"

# Create the chrome app and a single 'localhost' development app
MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

# then add additional apps by manifest
from bootstrap_helpers import bootstrap_codingsystems
from bootstrap_helpers import bootstrap_applications
