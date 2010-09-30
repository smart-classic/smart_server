from smart.models import *
from django.conf import settings
import os

# Create the chrome app and a single 'localhost' development app

MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')


a=PHA.objects.create(start_url_template= 'http://localhost:8000/index.html',
                   callback_url = 'http://localhost:8000/after_auth.html',
                   has_ui = True,
                   frameable = True,
                   description = 'Points to a locally-hosted app for development.',
                   consumer_key = 'developers-sandbox-app',
                   secret = 'smartapp-secret',
                   name ='Developers Sandbox',
                   email='developer-sandbox@apps.smart.org',
                   background_p=False)
AppActivity.objects.create(app=a, name='main')

# then add additional apps by manifest
from bootstrap_helpers import bootstrap_codingsystems
from bootstrap_helpers import bootstrap_demographics
from bootstrap_helpers import bootstrap_applications
