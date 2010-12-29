"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
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

  def get_demographic_rdf(self):
    c = DemographicConnector()

    q = Template("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/>
    CONSTRUCT  {
        <http://smartplatforms.org/records/$who/demographics> ?p ?o.
    } WHERE {
        <http://smartplatforms.org/records/$who/demographics> ?p ?o.
    }""").substitute(who=self.id)

    return c.sparql(q)

  @classmethod
  def search_records(cls, query):
    c = DemographicConnector()
    res = c.sparql(query)
    
    m = utils.parse_rdf(res)
    d = utils.default_ns()
    
    print "Got", res
    people = m.find_statements(RDF.Statement(None, d['rdf']['type'], d['foaf']['Person']))
    print "got all people ", utils.serialize_rdf(people)
    record_list = []
    for p in people:
        record = Record()
        print "working with person ", p
        record.id = re.search("\/records\/(.*?)\/", str(p.subject)).group(1)
        record.fn = list(m.find_statements(RDF.Statement(p.subject, d['foaf']['givenName'], None)))[0].object.literal_value['string']
        record.ln = list(m.find_statements(RDF.Statement(p.subject, d['foaf']['familyName'], None)))[0].object.literal_value['string']
        print "found the snames ", record.fn, record.ln, record.id
        print "demobirth", d['spdemo']['birthday']
        dob = list(m.find_statements(RDF.Statement(p.subject, d['spdemo']['birthday'], None)))[0].object.literal_value['string']
        record.dob = dob
        record_list.append(record)

    return record_list
    
class AccountApp(Object):
  account = models.ForeignKey(Account)
  app = models.ForeignKey(PHA)

  # uniqueness
  class Meta:
    app_label = APP_LABEL
    unique_together = (('account', 'app'),)
