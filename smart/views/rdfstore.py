"""
RDF Store for PHAs

Josh Mandel

"""

from base import *
from smart.lib import utils
from django.http import HttpResponseBadRequest
from django.conf import settings
import psycopg2
import psycopg2.extras
from rdflib import ConjunctiveGraph, Namespace, Literal
from StringIO import StringIO
import smart.models



SPARQL = 'SPARQL'
def default_ns():
   d = {}
   d['dc'] = Namespace('http://purl.org/dc/elements/1.1/')
   d['dcterms'] = Namespace('http://purl.org/rss/1.0/modules/dcterms/')
   d['med'] = Namespace('http://smartplatforms.org/med#')
   d['rdf'] = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
   d['rxn'] = Namespace("http://link.informatics.stonybrook.edu/rxnorm/")
   d['rxcui'] = Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXCUI/")
   d['rxaui'] = Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXAUI/")
   d['rxatn'] = Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXATN#")
   d['rxrel'] = Namespace("http://link.informatics.stonybrook.edu/rxnorm/REL#")
   d['ccr'] = Namespace("urn:astm-org:CCR")
   return d

def bind_ns(graph, ns=default_ns()):
    for k in ns.keys():
        graph.bind(k, ns[k])

def bound_graph():
    g = ConjunctiveGraph()
    bind_ns(g)
    return g 

    


# Replace the entire store with data passed in
def post_rdf (request, connector, maintain_existing_store=False):
    ct = utils.get_content_type(request).lower()
    
    if (ct != "application/rdf+xml"):
        raise Exception("RDF Store only knows how to store RDF+XML content.")
    
    g = bound_graph()
    triples = connector.get()
    
    if (maintain_existing_store and triples != ""):
        g.parse(StringIO(triples), publicID="existing") 
    
    g.parse(StringIO(request.raw_post_data), publicID="new") 
    triples = g.serialize()
    connector.set( triples )
    return HttpResponse(triples, mimetype="application/rdf+xml")

# Fetch the entire store and pass back rdf/xml -- or pass back partial graph 
# if a SPARQl CONSTRUCT query string is provided.
def get_rdf (request, connector):
   triples = connector.get()
   g = bound_graph()        

   if (triples != ""):
       g.parse(StringIO(triples)) 
   
   if (SPARQL not in request.GET.keys()):
       print "no sparql, so here's everything: ", triples
       return HttpResponse(triples, mimetype="application/rdf+xml")
   
   sq = request.GET[SPARQL]
   print "Sparkley ",sq, g.query(sq).serialize()
   return HttpResponse(g.query(sq).serialize(), mimetype="application/rdf+xml")

def put_rdf(request, connector):
    return post_rdf(request, connector, maintain_existing_store=True)

# delete all or a query-based subset of the store, returning deleted graph
def delete_rdf(request, connector):
   sparql = request.raw_post_data  
   triples = connector.get()

   if (not sparql.startswith(SPARQL)):
       connector.set("")
       return HttpResponse(triples, mimetype="application/rdf+xml")

   sparql = urllib.unquote_plus(sparql)[7:]
   print "and, ", sparql
   g = bound_graph()        
   deleted = bound_graph()
   
   if (triples != ""):
       g.parse(StringIO(triples)) 
    
   for r in g.query(sparql).result:
       deleted.add(r)
       g.remove(r)

   triples = g.serialize()
   connector.set( triples )
   print "deleted", deleted.serialize()    
   return HttpResponse(deleted.serialize(), mimetype="application/rdf+xml")


def post_rdf_store (request):
    c = PHAStoreConnector(request)
    return post_rdf(request, c)

def get_rdf_store (request):    
    c = PHAStoreConnector(request)
    return get_rdf(request, c)

def put_rdf_store(request):
    c = PHAStoreConnector(request)
    return put_rdf(request, c)

def delete_rdf_store(request):
    c = PHAStoreConnector(request)
    return delete_rdf(request, c)

def post_rdf_meds (request):
    rdf = utils.meds_as_rdf(request.raw_post_data) 
    c = MedStoreConnector(request)
    c.set(rdf)
    return HttpResponse(rdf, mimetype="application/rdf+xml")

def get_rdf_meds (request, record_id=None):    
    c = MedStoreConnector(request, record_id)
    return get_rdf(request, c)

def put_rdf_meds(request):
    c = MedStoreConnector(request)
    return put_rdf(request, c)

def delete_rdf_meds(request):
    c = MedStoreConnector(request)
    return delete_rdf(request, c)

class PHAStoreConnector():
    def __init__(self, request):
        self.pha = request.principal
        if not (isinstance(self.pha, smart.models.PHA)):
            raise Exception("RDF Store only stores data for PHAs.")
        try:
            self.object = smart.models.PHA_RDFStore.objects.get(PHA=self.pha)
        except:
            self.object = smart.models.PHA_RDFStore.objects.create(PHA=self.pha)
        
    def get(self):    
        return self.object.triples
    
    def set(self, triples):
        self.object.triples = triples
        self.object.save()
        
class MedStoreConnector():
    def __init__(self, request, record_id=None):
        at = request.principal
        
        if (record_id == None):       
            if not (isinstance(at, smart.models.AccessToken)):
                raise Exception("Med Store request must be signed with an access token.")    
            self.record = at.share.record
        else:
            self.record = Record.objects.get(id=record_id)

        try:
            self.object = smart.models.Medication.objects.get(record=self.record)
        except:
            self.object = smart.models.Medication.objects.create(record=self.record)
        
    def get(self):    
        return self.object.triples
    
    def set(self, triples):
        self.object.triples = triples
        self.object.save()