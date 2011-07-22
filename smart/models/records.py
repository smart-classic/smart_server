"""
Records for SMART Reference EMR

Ben Adida & Josh Mandel
"""

from base import *
from django.utils import simplejson
from smart.common.util import rdf, foaf, sp, serialize_rdf, parse_rdf, bound_graph, URIRef, Namespace
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from smart.models.rdf_store import DemographicConnector, RecordStoreConnector
from string import Template
import re, datetime

class Record(Object):
  Meta = BaseMeta()

  full_name = models.CharField(max_length = 150, null= False)

  def __unicode__(self):
    return 'Record %s' % self.id

  def query(self):

    q = Template("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/terms#>
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

    # for each person, look up their demographics object.
    from smart.models.record_object import RecordObject
    people = m.triples((None, rdf['type'], sp.Demographics))
    pobj = RecordObject[sp.Demographics] 

    return_graph = bound_graph()
    for person in people:
      p = person[0] # subject

      # Connect to RDF Store
      pid = re.search("\/records\/(.*?)\/demographics", str(p)).group(1)
      print "matched ", p," to ", pid
      c = RecordStoreConnector(Record.objects.get(id=pid))

      # Pull out demographics
      p_uri = p.n3() # subject URI
      p_subgraph = parse_rdf(c.sparql(pobj.query_one(p_uri)))
      print "subgraph: ", serialize_rdf(p_subgraph)
      
      # Append to search result graph
      return_graph += p_subgraph
    print "got", serialize_rdf(return_graph)
    return serialize_rdf(return_graph)

  @classmethod
  def rdf_to_objects(cls, res):
    m = parse_rdf(res)
    
    print "Mapping RDF to objects...", res
    people = m.triples((None, rdf['type'], sp.Demographics))
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


class RecordAlert(Object):
  record=models.ForeignKey(Record)
  alert_text =  models.TextField(null=False)
  alert_time = models.DateTimeField(auto_now_add=True, null=False)
  triggering_app = models.ForeignKey('OAuthApp', null=False, related_name='alerts')
  acknowledged_by = models.ForeignKey('Account', null=True)
  acknowledged_at = models.DateTimeField(null=True)

  # uniqueness
  class Meta:
    app_label = APP_LABEL
  
  @classmethod
  def from_rdf(cls, rdfstring, record, app):
    s = parse_rdf(rdfstring)

    q = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX sp: <http://smartplatforms.org/terms#>
    SELECT ?notes ?severity
    WHERE {
          ?a rdf:type sp:Alert.
          ?a sp:notes ?notes.
          ?a sp:severity ?scv.
          ?scv sp:code ?severity.
    }"""

    r = list(s.query(q))
    assert len(r) == 1, "Expected one alert in post, found %s"%len(r)
    (notes, severity) = r[0]

    assert type(notes) == Literal
    spcodes = Namespace("http://smartplatforms.org/terms/code/alertLevel#")
    assert severity in [spcodes.information, spcodes.warning, spcodes.critical]

    a = RecordAlert(record=record, 
                    alert_text=str(notes), 
                    triggering_app=app)
    a.save()
    return a

  def acknowledge(self, account):
    self.acknowledged_by =  account
    self.acknowledged_at = datetime.datetime.now()
    self.save()
