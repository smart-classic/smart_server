from django.conf import settings
from smart.models import *
from string import Template
import re
import sys
import os
from django.utils import simplejson
import urllib2

def sub(str, var, val):
    return str.replace("{%s}"%var, val)

# Some basic apps and a couple of accounts to get things going.

apps = simplejson.loads(open(os.path.join(settings.APP_HOME, 
                                          "bootstrap_helpers/application_list.json")).read())
apps = apps["app_list"]
for app,app_params in apps.iteritems():
  print app
  base_url = re.search("https?://.*?[/$]", app).group()[:-1]
  s = urllib2.urlopen(app)
  r = simplejson.loads(s.read())

  enabled_by_default = app_params["enabled_by_default"] 

  if ('base_url' not in locals()):
    base_url = r["base_url"]
  
  if r["mode"] == "background" or r["mode"] == "helper":
      admin_p = False
      try:
          admin_p =  app_params["admin_p"]
      except: pass

      a = HelperApp.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"],
                       admin_p = admin_p)
      
  elif r["mode"] == "ui":
      a = PHA.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"],
                       icon_url=sub(r["icon"], "base_url", base_url),
                       enabled_by_default=enabled_by_default)
  else: a = None

  try:
    for (act_name, act_url) in r["activities"].iteritems():
      act_url = sub(act_url, "base_url", base_url)
      AppActivity.objects.create(app=a, name=act_name, url=act_url)
  except: pass

  try:
    for (hook_name, hook_data) in r["web_hooks"].iteritems():
      hook_url = sub(hook_data["url"], "base_url", base_url)

      try: rpc = hook_data['requires_patient_context']
      except: rpc = False
      
      AppWebHook.objects.create(app=a,
                              name=hook_name, 
                              description=hook_data["description"],
                              url=hook_url,
                              requires_patient_context=rpc)
  except: pass
  print "done ", app
  s.close() 
