"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.common.util import rdf, foaf, sp, serialize_rdf, parse_rdf
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from smart.models.rdf_store import DemographicConnector
from string import Template
import RDF, re

class Record(Object):
  Meta = BaseMeta()

  full_name = models.CharField(max_length = 150, null= False)

  def __unicode__(self):
    return 'Record %s' % self.id

  def query(self):

    q = Template("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/>
    CONSTRUCT  {
        <http://smartplatforms.org/records/$who/demographics> ?p ?o.
    } WHERE {
        <http://smartplatforms.org/records/$who/demographics> ?p ?o.
    }""").substitute(who=self.id)

    return q

  def get_demographic_rdf(self):
    c = DemographicConnector()
    q = self.query()
    return c.sparql(q)

  @classmethod
  def search_records(cls, query):
    c = DemographicConnector()
    res = c.sparql(query)
    
    m = parse_rdf(res)
    
    print "Got", res
    people = m.find_statements(RDF.Statement(None, rdf['type'], foaf['Person']))
    record_list = []
    for p in people:
        record = Record()
        print "working with person ", p, str(p.subject.uri), p.subject.is_resource() 
        record.id = re.search("\/records\/(.*?)\/demographics", str(p.subject.uri)).group(1)
        record.fn = list(m.find_statements(RDF.Statement(p.subject, foaf['givenName'], None)))[0].object.literal_value['string']
        record.ln = list(m.find_statements(RDF.Statement(p.subject, foaf['familyName'], None)))[0].object.literal_value['string']
        print "found the snames ", record.fn, record.ln, record.id
        dob = list(m.find_statements(RDF.Statement(p.subject, sp['birthday'], None)))[0].object.literal_value['string']
        record.dob = dob

        gender = list(m.find_statements(RDF.Statement(p.subject, foaf['gender'], None)))[0].object.literal_value['string']
        record.gender = gender

        zipcode = list(m.find_statements(RDF.Statement(p.subject, sp['zipcode'], None)))[0].object.literal_value['string']
        record.zipcode = zipcode
       
        record_list.append(record)

    return record_list
    
class AccountApp(Object):
  account = models.ForeignKey(Account)
  app = models.ForeignKey(PHA)

  # uniqueness
  class Meta:
    app_label = APP_LABEL
    unique_together = (('account', 'app'),)
