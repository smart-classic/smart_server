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


a=PHA.objects.create(description = 'Points to a locally-hosted app for development.',
                   consumer_key = 'developers-sandbox-app',
                   secret = 'smartapp-secret',
                   name ='Developers Sandbox',
                   email='developer-sandbox@apps.smart.org',
                   icon_url="http://sandbox.smartplatforms.org/static/resources/images/app_icons_32/developers_sandbox.png"
                     )
AppActivity.objects.create(app=a, name='main', url='http://localhost:8000/index.html')
AppActivity.objects.create(app=a, name='after_auth', url='http://localhost:8000/after_auth.html')

print "BOOTSTRAP helpers"
# then add additional apps by manifest
from bootstrap_helpers import bootstrap_codingsystems
print "done cs"
from bootstrap_helpers import bootstrap_demographics
print "done demographics"
from bootstrap_helpers import bootstrap_applications
print "done apps"
