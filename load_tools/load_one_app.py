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

def LoadApp(app, enabled_by_default=False):
    # Some basic apps and a couple of accounts to get things going.
  print app
  if not app.startswith("http"):
      s = open(app)
      base_url = None
  else:
      base_url = re.search("https?://.*?[/$]", app).group()[:-1]
      s = urllib2.urlopen(app)

  manifest_string = s.read()
  s.close() 
  LoadAppFromJSON(manifest_string, enabled_by_default)

def LoadAppFromJSON(manifest_string, enabled_by_default, base_url=None):
  r = simplejson.loads(manifest_string)
  if base_url == None:
      try:
          base_url = r["base_url"]
      except:
          base_url = "unknown"
  
  manifest_string = manifest_string.replace("{base_url}", base_url)

  if r["mode"] == "background" or r["mode"] == "helper":
      a = HelperApp.objects.create(
                       description = r["description"],
                       consumer_key = r["id"],
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"],
                       manifest=manifest_string)
      
  elif r["mode"] == "ui" or r["mode"] == "frame_ui":

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
                       secret = 'smartapp-secret',
                       name =r["name"],
                       email=r["id"],
                       mode=r["mode"],
                       icon_url=sub(r["icon"], "base_url", base_url),
                       enabled_by_default=enabled_by_default,
                       optimal_environments=",".join(r["optimalBrowserEnvironments"]),
                       supported_environments=",".join(r["supportedBrowserEnvironments"]),
                       manifest=manifest_string)
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

if __name__ == "__main__":
    import string
    for v in sys.argv[1:]:
        print "Loading app: %s"%v
        LoadApp(v)

