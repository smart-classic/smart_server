
from smart.models import *
from django.conf import settings

# Some basic apps and a couple of accounts to get things going.

MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

PHA.objects.create(start_url_template= 'http://localhost:8001/meds.html?record_id={record_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'List patient\'s medications plus supplementary details',
                   consumer_key = 'smart-fg-app',
                   secret = 'smartapp-secret',
                   name ='MedList',
                   email='medlist@apps.smart.org')

PHA.objects.create(start_url_template= 'http://localhost:8001/problems.html?record_id={record_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'Interactive Problem List Editor',
                   consumer_key = 'smart-problems-app',
                   secret = 'smartapp-secret',
                   name ='Problems',
                   email='smart-problems@apps.smart.org')



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

a2 = Account.objects.create(email = 'joshmandel@smart.org', full_name='Josh Mandel', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='joshmandel', password='test')

a2 = Account.objects.create(email = 'test@smart.org', full_name='Test User', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='test', password='test')

# create a couple of records

ss_1 = Record.objects.create(full_name = 'Hiram Bach')
ss_2 = Record.objects.create(full_name = 'Bert Schnur')
ss_4 = Record.objects.create(full_name = 'Bruce Paltrow')
ss_5 = Record.objects.create(full_name = 'David Cross')
ss_6 = Record.objects.create(full_name = 'Hans Bergermeister')
ss_7 = Record.objects.create(full_name = 'Mary Paltrow')
ss_8 = Record.objects.create(full_name = 'Tad Dockendorf')
ss_9 = Record.objects.create(full_name = 'Nora Bergermeister')
ss_10 = Record.objects.create(full_name = 'Bob Odenkirk')
ss_11 = Record.objects.create(full_name = 'Douglas Richardson')

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
  <foaf:familyName>Bach</foaf:familyName>
  <foaf:givenName>Hiram</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>02543</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Schnur</foaf:familyName>
  <foaf:givenName>Bert</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>63050</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Bruce</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>54360</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Cross</foaf:familyName>
  <foaf:givenName>David</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>08608</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Hans</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>19013</sp:zipcode>
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

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Nora</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>19013</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Odenkirk</foaf:familyName>
  <foaf:givenName>Bob</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <sp:zipcode>90001</sp:zipcode>
</rdf:Description>

<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Richardson</foaf:familyName>
  <foaf:givenName>Douglas</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <sp:zipcode>01040</sp:zipcode>
</rdf:Description>

</rdf:RDF>""" % ( 
 ss_1.id,
 ss_2.id,
 ss_4.id, # for some reasont the SS Test set has no element 3(?) -JM
 ss_5.id,
 ss_6.id,
 ss_7.id,
 ss_8.id,
 ss_9.id,
 ss_10.id,
 ss_11.id)

p = Problem(record=ss_1, triples = """<?xml version="1.0" encoding="utf-8"?>
<rdf:RDF  xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:sp="http://smartplatforms.org/" xmlns:umls="http://www.nlm.nih.gov/research/umls/" xmlns:dcterms="http://purl.org/dc/terms/">
         <rdf:Description>
            <rdf:type rdf:resource="http://smartplatforms.org/problem"/>
            <umls:cui>C0027424</umls:cui>
            <dcterms:title>Nasal congestion (Finding)</dcterms:title>
            <sp:onset>2008-12-14</sp:onset>
            <sp:resolution>2009-02-01</sp:resolution>
            <sp:notes>Congestion worst on first waking up.</sp:notes>
         </rdf:Description>
</rdf:RDF>
""")
p.save()

model = RDF.Model(storage=rs)
parser = RDF.Parser()
parser.parse_string_into_model(model, bios.encode(),"bootstrap_context")
