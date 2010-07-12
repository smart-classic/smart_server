"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from string import Template
import RDF

class Record(Object):
  Meta = BaseMeta()

  full_name = models.CharField(max_length = 150, null= False)

  def __unicode__(self):
    return 'Record %s' % self.id

  def get_demographic_rdf(self):
    m = utils.get_backed_model()
    q = Template("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/>
    CONSTRUCT  {
        <http://smartplatforms.org/records/$who> ?p ?o.
    } WHERE {
        <http://smartplatforms.org/records/$who> ?p ?o.
    }""").substitute(who=self.id)

    print "QUERYING", q
    q = RDF.SPARQLQuery(q.encode())
    
    ret = RDF.Model()
    for s in q.execute(m).as_stream():
        ret.append(s)
    
    return utils.serialize_rdf(ret)

  @staticmethod
  def create_or_bind_from_rdf(demographics):
    
    q = RDF.SPARQLQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/>
    SELECT DISTINCT ?s, ?gn, ?fn, ?zip, ?gender
    WHERE {
        ?s rdf:type foaf:Person.
        ?s foaf:givenName ?gn.
        ?s foaf:familyName ?fn.
        ?s sp:zipcode ?zip.
        ?s foaf:gender ?gender.
    }""")
    print q
          
    r =  q.execute(demographics)
    r = r.next()

    givenName = r['gn'].literal_value['string']
    familyName = r['fn'].literal_value['string']
    zipcode = r['zip'].literal_value['string']
    gender = r['gender'].literal_value['string']
    subject = r['s']
        
    print givenName, familyName, zipcode, gender, subject
    
    model = utils.get_backed_model()
    q = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX foaf:   <http://xmlns.com/foaf/0.1/>
    PREFIX sp: <http://smartplatforms.org/>
    SELECT DISTINCT ?s 
    WHERE {
        ?s rdf:type foaf:Person.
        ?s foaf:givenName '%s'.
        ?s foaf:familyName '%s'.
        ?s sp:zipcode '%s'.
        ?s foaf:gender '%s'.
    }""" % (givenName, familyName, zipcode, gender)
    q = q.encode()
    print q
    
    q = RDF.SPARQLQuery(q)
    
    r = q.execute(model)
    try:
        r = r.next()
        id = utils.strip_ns(r['s'], "http://smartplatforms.org/records/")
        return Record.objects.get(id=id)
    except StopIteration:    
         # TODO:  normalize these fields to RDF, not the Record model
        r = Record.objects.create(full_name = "%s %s" % (givenName, familyName))
        subjectURI = RDF.Node(uri_string="http://smartplatforms.org/records/%s"%r.id)
        for s in demographics:
            if (s.subject == subject):
                s.subject = subjectURI
            try:
                model.append(s)
            except RDF.RedlandError:
                pass #todo: REALLY need to figure out the cause of this (text-encoding?) error!
                
        return r
        
    raise Exception("Couldn't find or bind demographics from RDF")

class AccountApp(Object):
  account = models.ForeignKey(Account)
  app = models.ForeignKey(PHA)

  # uniqueness
  class Meta:
    app_label = APP_LABEL
    unique_together = (('account', 'app'),)
