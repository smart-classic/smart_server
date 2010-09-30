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
  base_url = re.search("https?://.*?[/$]", app).group()
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

sys.exit(1)

MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')



ha = HelperApp.objects.create(
                   description = 'Provides basic implementation of fuzzy_match_rxnorm webhook, as a service to other apps',
                   consumer_key = 'basic-fuzzy-match-app-key',
                   secret = 'smartapp-secret',
                   name ='Basic Fuzzy Match',
                   email='basic-fuzzy-match-app@apps.smart.org'
                  )

h = AppWebHook.objects.create(app=ha, name='fuzzy_match_rxnorm', description='webhookt to fuzzy-match a text description of a drug to a set of matching RxNorm Concepts', url='http://192.168.1.103:8001/webhook/fuzzy_match_rxnorm')

a=PHA.objects.create(start_url_template= 'http://192.168.1.103:8001/nlp_import.html',
                   callback_url = '',
                   has_ui = True,
                   frameable = True,
                   description = 'Import medications from a plaintext clinical note.',
                   consumer_key = 'nlp-import-app',
                   secret = 'smartapp-secret',
                   name ='NLP Meds',
                   email='nlp-import@apps.smart.org',
                   background_p=False)
AppActivity.objects.create(app=a, name='main')



a=PHA.objects.create(start_url_template= 'http://192.168.1.103:8001/framework/med_batch_add/med_batch_add.html',
                   callback_url = '',
                   has_ui = True,
                   frameable = True,
                   description = 'Add a batch of medications to a patient record',
                   consumer_key = 'med-bach-add-app',
                   secret = 'smartapp-secret',
                   name ='Med Batch Add',
                   email='med-batch-add@apps.smart.org',
                   background_p=False)
AppActivity.objects.create(app=a, name='batch_add_medications')



ha = HelperApp.objects.create(
                   description = 'Provides NLP-based medication extraction from free-text notes',
                   consumer_key = 'med-extraction-app-key',
                   secret = 'smartapp-secret',
                   name ='Med Extraction NLP',
                   email='med-extraction-nlp@apps.smart.org'
                  )

h = AppWebHook.objects.create(app=ha, name='extract_meds_from_plaintext', description='webhook to extract meds from plaintext', url='http://localhost:8001/webhook/extract_meds_from_plaintext')



"""
a = Account.objects.create(email = 'benadida@smart.org', full_name='Ben Adida', contact_email = 'ben@adida.net')
a.set_username_and_password(username='benadida', password='test')

a2 = Account.objects.create(email = 'joshmandel@smart.org', full_name='Josh Mandel', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='joshmandel', password='test')

a2 = Account.objects.create(email = 'test@smart.org', full_name='SMArt Developer', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='developer', password='test')
"""
# create a couple of records

bios = []
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bach</foaf:familyName>
  <foaf:givenName>Hiram</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>02543</sp:zipcode>
  <sp:birthday>19631215</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Schnur</foaf:familyName>
  <foaf:givenName>Bert</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>63050</sp:zipcode>
  <sp:birthday>19450419</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Bruce</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>54360</sp:zipcode>
  <sp:birthday>19450201</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Cross</foaf:familyName>
  <foaf:givenName>David</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>08608</sp:zipcode>
  <sp:birthday>19720910</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Hans</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>19013</sp:zipcode>
  <sp:birthday>19631201</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Mary</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>54360</sp:zipcode>
  <sp:birthday>19510618</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Dockendorf</foaf:familyName>
  <foaf:givenName>Tad</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>82001</sp:zipcode>
  <sp:birthday>19750705</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Nora</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>19013</sp:zipcode>
  <sp:birthday>19641009</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Odenkirk</foaf:familyName>
  <foaf:givenName>Bob</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>90001</sp:zipcode>
  <sp:birthday>19591225</sp:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Richardson</foaf:familyName>
  <foaf:givenName>Douglas</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>01040</sp:zipcode>
  <sp:birthday>19680901</sp:birthday>
</rdf:Description>
""")

from smart.views.rdfstore import record_demographics_put_helper
for b in bios:
  ss_patient = Record.objects.create(full_name = 'noname')
  req = Object()
  req.raw_post_data = """<?xml version="1.0"?>
   <rdf:RDF
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:sp="http://smartplatforms.org/"
     xmlns:foaf="http://xmlns.com/foaf/0.1/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:dcterms="http://purl.org/dc/terms/"
     xmlns:bio="http://purl.org/vocab/bio/0.1/">
   %s
   </rdf:RDF>"""%(b%ss_patient.id)

  record_demographics_put_helper(req,ss_patient)

interpolated_postgres_load(
    os.path.join(settings.APP_HOME, "codingsystems/data/load-snomedctcore.sql"),
    {"snomed_core_data": 
     os.path.join(settings.APP_HOME, 
                  "codingsystems/data/complete/SNOMEDCT_CORE_SUBSET_201005.utf8.txt")},
    settings.DATABASE_NAME,
    settings.DATABASE_USER
)
