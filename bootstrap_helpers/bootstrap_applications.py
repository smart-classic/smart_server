from bootstrap_utils import interpolated_postgres_load, put_rdf
from django.conf import settings
from smart.models import *
from string import Template
import re
import sys
import os
import simplejson
import urllib2

def sub(str, var, val):
    return str.replace("{%s}"%var, val)

# Some basic apps and a couple of accounts to get things going.

apps = simplejson.loads(open(os.path.join(settings.APP_HOME, "bootstrap_helpers/application_list.json")).read())
apps = apps["app_list"]

for app in apps:
  print app
  base_url = re.search("https?://.*?[/$]", app).group()[:-1]
  s = urllib2.urlopen(app)
  r = simplejson.loads(s.read())

  if ('base_url' not in locals()):
    base_url = r["base_url"]
  
  if r["mode"] == "background" or r["mode"] == "helper":
      a = HelperApp.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"])
  elif r["mode"] == "ui":
      a = PHA.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"],
                       icon_url=sub(r["icon"], "base_url", base_url))
  else: a = None
  
  try:
    for (act_name, act_url) in r["activities"].iteritems():
      act_url = sub(act_url, "base_url", base_url)
      AppActivity.objects.create(app=a, name=act_name, url=act_url)
  except: pass

  try:
    for (hook_name, hook_data) in r["web_hooks"].iteritems():
      hook_url = sub(hook_data["url"], "base_url", base_url)
      AppWebHook.objects.create(app=a,
                              name=hook_name, 
                              description=hook_data["description"],
                              url=hook_url)
  except: pass
  print "done ", app
  s.close()
