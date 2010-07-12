
from smart.models import *
from django.conf import settings

# Some basic apps and a couple of accounts to get things going.

MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

PHA.objects.create(start_url_template= 'http://localhost:8001/index.html?record_id={record_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'List patient\'s medications plus supplementary details',
                   consumer_key = 'smart-fg-app',
                   secret = 'smartapp-secret',
                   name ='MedList',
                   email='medlist@apps.smart.org')


PHA.objects.create(start_url_template= 'http://localhost:8001/statin.html?record_id={record_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'States whether patient is taking a statin.',
                   consumer_key = 'smart-statin-app',
                   secret = 'smartapp-secret',
                   name ='Am-I-on-a-Statin?',
                   email='am-i-on-a-statin@apps.smart.org')


PHA.objects.create(start_url_template= 'http://localhost:8002/smart/start_auth?record_id={record_id}',
                   callback_url = 'http://localhost:8002/smart/after_auth',
                   has_ui = True,
                   frameable = True,
                   description = 'Keeps SMArt updated from a SureScripts feed (long-term, runs in background)',
                   consumer_key = 'smart-bg-app',
                   secret = 'smartapp-secret',
                   name ='SureScripts Sync',
                   email='surescripts-sync@apps.smart.org',
                   background_p=True)

a = Account.objects.create(email = 'benadida@smart.org', full_name='Ben Adida', contact_email = 'ben@adida.net')
a.set_username_and_password(username='benadida', password='test')

# create a couple of records
r1_john = Record.objects.create(full_name = 'John Doe')
r1_jane = Record.objects.create(full_name = 'Jane Doe')


a2 = Account.objects.create(email = 'joshmandel@smart.org', full_name='Josh Mandel', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='joshmandel', password='test')

# create a couple of records

r2_john = Record.objects.create(full_name = 'John Smith')
r2_jane = Record.objects.create(full_name = 'Jane Smith')

ss_1 = Record.objects.create(full_name = 'Hiram Bach')
ss_2 = Record.objects.create(full_name = 'Mary Paltrow')
ss_3 = Record.objects.create(full_name = 'Tad Dockendorf')

import RDF

db = settings.DATABASE_REDLAND
u = settings.DATABASE_USER
p =settings.DATABASE_PASSWORD
rs = RDF.Storage(storage_name="postgresql", name=db, 
         options_string="new='yes',database='%s',host='localhost',user='%s',password='%s',contexts='yes'"%
         (db, u, p))

bios = """<?xml version="1.0"?>

<rdf:RDF
xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
xmlns:sp="http://smartplatforms.org/"
xmlns:foaf="http://xmlns.com/foaf/0.1/"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:dcterms="http://purl.org/dc/terms/"
xmlns:bio="http://purl.org/vocab/bio/0.1/"
>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Smith</foaf:familyName>
  <foaf:givenName>John</foaf:givenName>
  <foaf:title>Mr.</foaf:title>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>02149</sp:zipcode>
  <bio:Birth> <rdf:Description><dc:date>1970-10-01</dc:date></rdf:Description></bio:Birth>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Doe</foaf:familyName>
  <foaf:givenName>John</foaf:givenName>
  <foaf:title>Mr.</foaf:title>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>02249</sp:zipcode>
  <bio:Birth> <rdf:Description><dc:date>1950-03-20</dc:date></rdf:Description></bio:Birth>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Doe</foaf:familyName>
  <foaf:givenName>Jane</foaf:givenName>
  <foaf:title>Miss</foaf:title>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>06039</sp:zipcode>
  <bio:Birth> <rdf:Description><dc:date>1996-04-30</dc:date></rdf:Description></bio:Birth>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Smith</foaf:familyName>
  <foaf:givenName>Jane</foaf:givenName>
  <foaf:title>Mrs</foaf:title>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>90201</sp:zipcode>
  <bio:Birth> <rdf:Description><dc:date>1980-08-12</dc:date></rdf:Description></bio:Birth>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bach</foaf:familyName>
  <foaf:givenName>Hiram</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>02543</sp:zipcode>
</rdf:Description>
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Mary</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>54360</sp:zipcode>
</rdf:Description>
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Dockendorf</foaf:familyName>
  <foaf:givenName>Tad</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>82001</sp:zipcode>
</rdf:Description>

</rdf:RDF>""" % (r2_john.id.encode(), r1_john.id.encode(), r1_jane.id.encode(), r2_jane.id.encode(), ss_1.id.encode(), ss_2.id.encode(), ss_3.id.encode())

model = RDF.Model(storage=rs)
parser = RDF.Parser()
parser.parse_string_into_model(model, bios.encode(),"bootstrap_context")
