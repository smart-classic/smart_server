print "BOOTSTRAP"
from smart.models import *
from django.conf import settings
import os, sys
import traceback
print "DONE BOOTSTRAP imports"

# Create the chrome app and a single 'localhost' development app
print "Creating ma"
MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

print "Creating deva"
a=PHA.objects.create(description = 'Points to a locally-hosted app for development.',
                   consumer_key = 'my-app@apps.smartplatforms.org',
                   secret = 'smartapp-secret',
                   name ='My App',
                   email='my-app@apps.smartplatforms.org',
                   icon_url="http://sandbox.smartplatforms.org/static/resources/images/app_icons_32/developers_sandbox.png",
                     enabled_by_default=True
                     )

AppActivity.objects.create(app=a, name='main', url='http://localhost:8000/smartapp/bootstrap.html')


print "Creating devc"
a=PHA.objects.create(description = 'Points to a cloud-hosted app for development.',
                   consumer_key = 'my-cloud-app@apps.smartplatforms.org',
                   secret = 'smartapp-secret',
                   name ='My Cloud App',
                   email='my-cloud-app@apps.smartplatforms.org',
                   icon_url="http://sandbox.smartplatforms.org/static/resources/images/app_icons_32/developers_sandbox.png",
                     enabled_by_default=False
                     )

AppActivity.objects.create(app=a, name='main', url='http://localhost:8000/smartapp/bootstrap.html')


print "BOOTSTRAP helpers"
# then add additional apps by manifest
from bootstrap_helpers import bootstrap_codingsystems
print "done cs"
from bootstrap_helpers import bootstrap_demographics
print "done demographics"
from bootstrap_helpers import bootstrap_applications
print "done apps"
