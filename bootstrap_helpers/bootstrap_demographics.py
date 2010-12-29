from django.conf import settings
from bootstrap_utils import interpolated_postgres_load
import os, glob

bios = []
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bach</foaf:familyName>
  <foaf:givenName>Hiram</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>02543</spdemo:zipcode>
  <spdemo:birthday>1963-12-15</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Schnur</foaf:familyName>
  <foaf:givenName>Bert</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>63050</spdemo:zipcode>
  <spdemo:birthday>1945-04-19</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Bruce</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>54360</spdemo:zipcode>
  <spdemo:birthday>1945-02-01</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Cross</foaf:familyName>
  <foaf:givenName>David</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>08608</spdemo:zipcode>
  <spdemo:birthday>1972-09-10</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Hans</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>19013</spdemo:zipcode>
  <spdemo:birthday>1963-12-01</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Paltrow</foaf:familyName>
  <foaf:givenName>Mary</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <spdemo:zipcode>54360</spdemo:zipcode>
  <spdemo:birthday>1951-06-18</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Dockendorf</foaf:familyName>
  <foaf:givenName>Tad</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>82001</spdemo:zipcode>
  <spdemo:birthday>1975-07-05</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Bergermeister</foaf:familyName>
  <foaf:givenName>Nora</foaf:givenName>
  <foaf:gender>female</foaf:gender>
  <spdemo:zipcode>19013</spdemo:zipcode>
  <spdemo:birthday>1964-10-09</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Odenkirk</foaf:familyName>
  <foaf:givenName>Bob</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>90001</spdemo:zipcode>
  <spdemo:birthday>1959-12-25</spdemo:birthday>
</rdf:Description>
""")
bios.append("""
<rdf:Description rdf:about="http://smartplatforms.org/records/%s">
  <rdf:type rdf:resource="http://xmlns.com/foaf/0.1/Person"/>
  <foaf:familyName>Richardson</foaf:familyName>
  <foaf:givenName>Douglas</foaf:givenName>
  <foaf:gender>male</foaf:gender>
  <spdemo:zipcode>01040</spdemo:zipcode>
  <spdemo:birthday>1968-09-01</spdemo:birthday>
</rdf:Description>
""")
print "Appending bios"

from smart.models import *
from smart.models.rdf_ontology import ontology

print "models imported"
from smart.views.smarthacks import put_demographics
print "put_demo imported"
print "total # to append", len(bios)
count=2000000000
for b in bios:
  id="%03d"%count
  count += 1
  print "creating record", id
  ss_patient = Record.objects.create(id=id)
  print "created record."
  req = Object()

  req.path = "/records/%s/demographics"%id
  req.raw_post_data = """<?xml version="1.0"?>
   <rdf:RDF
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:spdemo="http://smartplatforms.org/clinical/demographics#"
     xmlns:foaf="http://xmlns.com/foaf/0.1/"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:dcterms="http://purl.org/dc/terms/"
     xmlns:bio="http://purl.org/vocab/bio/0.1/">
   %s
   </rdf:RDF>"""%(b%id)
  
  print "putting ", id
  put_demographics(req, id, "http://xmlns.com/foaf/0.1/Person", ontology=ontology)
  print "done putting ", id
