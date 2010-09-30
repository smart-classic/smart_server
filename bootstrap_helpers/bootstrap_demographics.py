from bootstrap_utils import interpolated_postgres_load, put_rdf
from smart.models import *

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
