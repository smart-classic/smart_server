from django.conf import settings
from smart.models import *
from string import Template
import re
import sys
import os
from django.utils import simplejson
import urllib2
from load_tools.load_one_app import LoadApp, LoadAppFromJSON

def sub(str, var, val):
    return str.replace("{%s}"%var, val)

# Some basic apps and a couple of accounts to get things going.

apps = simplejson.loads(open(os.path.join(settings.APP_HOME, 
                                          "bootstrap_helpers/application_list.json")).read())

apps = apps["app_list"]
for app,app_params in apps.iteritems():

  enabled_by_default = app_params["enabled_by_default"] 

  LoadApp(app, enabled_by_default)


my_app = """
{
  "name" : "My App",
  "description" : "Points to a locally-hosted app for development",
  "author" : "Josh Mandel, Children's Hospital Boston",
  "id" : "my-app@apps.smartplatforms.org",
  "version" : ".1a",
  "mode" : "ui",

  "activities" : {
    "main" : "http://localhost:8000/smartapp/index.html"
  },
	
  "web_hooks" : { },

  "icon" :  "http://sandbox.smartplatforms.org/static/smart_ui_server/resources/images/app_icons_32/developers_sandbox.png"
}
"""

LoadAppFromJSON(my_app, True)
