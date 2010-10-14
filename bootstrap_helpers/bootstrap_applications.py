from string import Template
from smart.models import *
from bootstrap_utils import interpolated_postgres_load, put_rdf
from django.conf import settings
import re, sys, os
import simplejson
import urllib2

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

  a = PHA.objects.create(
                   description = r["description"],
                   consumer_key = r["id"],
                   secret = 'smartapp-secret',
                   name =r["name"],
                   email=r["id"])

  try:
    for (act_name, act_url) in r["activities"].iteritems():
      act_url = Template(act_url).substitute(base_url=base_url)
      AppActivity.objects.create(app=a, name=act_name, url=act_url)
  except: pass

  try:
    for (hook_name, hook_data) in r["web_hooks"].iteritems():
      hook_url = Template(hook_data["url"]).substitute(base_url=base_url)
      AppWebHook.objects.create(app=a,
                              name=hook_name, 
                              description=hook_data["description"],
                              url=hook_url)
  except: pass
  print "done ", app
  s.close()
