#!/usr/bin/env python

from django.conf import settings
from smart.models import *
from smart.lib.utils import get_capabilities, random_string
from string import Template
import re
import sys
import os
from django.utils import simplejson
import urllib2

# Import the manifest validator function
from smart.common.utils.manifest_tests import manifest_structure_validator

def sub(str, var, val):
    return str.replace("{%s}"%var, val)

def LoadApp(app_params):
    # Some basic apps and a couple of accounts to get things going.
  app = app_params["manifest"]
  print app
  if not app.startswith("http"):
      s = open(app)
  else:
      s = urllib2.urlopen(app)

  manifest_string = s.read()
  s.close() 
  return LoadAppFromJSON(manifest_string, app_params)
  
def LoadAppFromJSON(manifest_string, app_params=None):

  if app_params == None: app_params = {}

  if "secret" not in app_params:
    app_params["secret"] =  random_string(16)

  assert app_params != None, "Expected a consumer secret among the app params"
  r = simplejson.loads(manifest_string)
  secret = app_params["secret"]
 
  messages = manifest_structure_validator(r)
  if len(messages) > 0:
      print "WARNING! This app manifest is invalid"
      for m in messages:
        print m

  if "override_index" in app_params:
      r["index"] = app_params["override_index"]

  if "override_icon" in app_params:
      r["icon"] = app_params["override_icon"]

  enabled_by_default = False
  if "enabled_by_default" in app_params:
      enabled_by_default = app_params["enabled_by_default"]

  manifest_string = json.dumps(r, sort_keys=True, indent=4)

  if r["mode"] in ("background", "helper"):
      a = HelperApp.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = secret,
                       name =r["name"],
                       email=r["id"],
                       manifest=manifest_string)
      
  elif r["mode"] in ("ui", "frame_ui"):

      if "optimalBrowserEnvironments" not in r:
          r["optimalBrowserEnvironments"] = ["desktop"]
      if "supportedBrowserEnvironments" not in r:
          r["supportedBrowserEnvironments"] = ["desktop", "mobile", "tablet"]
              
      exists = PHA.objects.filter(email=r["id"])
      assert len(exists) <2, "Found >1 PHA by the name %s"%r["id"]
      if len(exists)==1:
          print exists[0]
          print "deleting, exists."
          exists[0].delete()

      a = PHA.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = secret,
                       name =r["name"],
                       email=r["id"],
                       mode=r["mode"],
                       icon_url=r["icon"],
                       enabled_by_default=enabled_by_default,
                       optimal_environments=",".join(r["optimalBrowserEnvironments"]),
                       supported_environments=",".join(r["supportedBrowserEnvironments"]),
                       manifest=manifest_string)
  else: a = None

  if "index" in r:
      act_name = "main"
      act_url  = r["index"]
      AppActivity.objects.create(app=a, name=act_name, url=act_url)
  
  if "requires" in r:  
    capabilities = get_capabilities()
    for k in r["requires"]:
        for m in r["requires"][k]["methods"]:
            if m not in capabilities[k]["methods"]:
                print "WARNING! This app requires an unsupported method:", k, m
                
  if "smart_version" in r:  
    if r["smart_version"] != settings.VERSION:
        print "WARNING! This app requires SMART version", r["smart_version"]

  if "web_hooks" in r:
    for (hook_name, hook_data) in r["web_hooks"].iteritems():
      hook_url = hook_data["url"]

      try: rpc = hook_data['requires_patient_context']
      except: rpc = False
      
      AppWebHook.objects.create(app=a,
                              name=hook_name, 
                              description=hook_data["description"],
                              url=hook_url,
                              requires_patient_context=rpc)
  return a

if __name__ == "__main__":
    import string
    v = sys.argv[1]
    secret = None

    if len(sys.argv)>2:
        secret = sys.argv[2]

    print "Loading apps via load_one_app is deprecated.  Please use 'python manage.py load_app' instead."
    print "Loading app: %s"%v

    app_params = {
        "manifest": v,
    }
    if secret:
        app_params["secret"] = secret

    a = LoadApp(app_params)
    print "Loaded app with secret: %s"%a.secret
