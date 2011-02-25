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
import re

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
    people = m.triples((None, rdf['type'], foaf['Person']))
    record_list = []
    for p in people:
        record = Record()
        print "working with person ", p
        record.id = re.search("\/records\/(.*?)\/demographics", str(p[0])).group(1)
        record.fn = str(list(m.triples((p[0], foaf['givenName'], None)))[0][2])
        record.ln = (list(m.triples((p[0], foaf['familyName'], None)))[0][2])
        print "found the snames ", record.fn, record.ln, record.id
        dob = str(list(m.triples((p[0], sp['birthday'], None)))[0][2])
        record.dob = dob

        gender = str(list(m.triples((p[0], foaf['gender'], None)))[0][2])
        record.gender = gender

        zipcode = str(list(m.triples((p[0], sp['zipcode'], None)))[0][2])
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
