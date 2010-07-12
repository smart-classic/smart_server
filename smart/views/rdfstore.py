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
import RDF
from StringIO import StringIO
import smart.models
from smart.lib.utils import parse_rdf, serialize_rdf, bound_graph

SPARQL = 'SPARQL'

# Replace the entire store with data passed in
def post_rdf (request, connector, maintain_existing_store=False):
    ct = utils.get_content_type(request).lower()
    
    if (ct != "application/rdf+xml"):
        raise Exception("RDF Store only knows how to store RDF+XML content.")
    
    g = bound_graph()
    triples = connector.get()
    
    if (maintain_existing_store and triples != ""):
        parse_rdf(triples, g, "existing") 
        
    parse_rdf(request.raw_post_data,g, "new")
   
    triples = serialize_rdf(g)
    connector.set( triples )
    
    return HttpResponse(triples, mimetype="application/rdf+xml")

# Fetch the entire store and pass back rdf/xml -- or pass back partial graph 
# if a SPARQl CONSTRUCT query string is provided.
def get_rdf (request, connector):
   triples = connector.get()
   g = bound_graph()        

   if (triples != ""):
       parse_rdf(triples, g)
   
   if (SPARQL not in request.GET.keys()):
       print "no sparql, so here's everything: ", triples
       return HttpResponse(triples, mimetype="application/rdf+xml")
   
   sq = request.GET[SPARQL].encode()
   print "Executing ", sq, " on ", triples, "-->", g
   q = RDF.SPARQLQuery(sq)
   res = q.execute(g)
   res_string = serialize_rdf(res)
   
   print "Sparkley ",sq, res_string
   return HttpResponse(res_string, mimetype="application/rdf+xml")

def put_rdf(request, connector):
    return post_rdf(request, connector, maintain_existing_store=True)

# delete all or a query-based subset of the store, returning deleted graph
def delete_rdf(request, connector):
   sparql = request.raw_post_data  
   triples = connector.get()

   if (not sparql.startswith(SPARQL)):
       connector.set("")
       return HttpResponse(triples, mimetype="application/rdf+xml")

   sparql = urllib.unquote_plus(sparql)[7:].encode()
   print "and, ", sparql
   g = bound_graph()        
   deleted = bound_graph()
   
   if (triples != ""):
       parse_rdf(triples, g)
    
   q = RDF.SPARQLQuery(sparql)
   res = q.execute(g)
   
   print "****\n\n\n\nmodl das", len(g)
   for r in res.as_stream():
       deleted.append(r)
       g.remove_statement(r)

   triples = serialize_rdf(g)
   connector.set( triples )
   print "deleted", serialize_rdf(deleted)    
   return HttpResponse(serialize_rdf(deleted), mimetype="application/rdf+xml")


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

@paramloader()
def post_rdf_meds (request, record):
    rdf = utils.meds_as_rdf(request.raw_post_data) 
    c = MedStoreConnector(request, record)
    c.set(rdf)
    return HttpResponse(rdf, mimetype="application/rdf+xml")

@paramloader()
def get_rdf_meds (request, record):    
    c = MedStoreConnector(request, record)
    return get_rdf(request, c)

@paramloader()
def put_rdf_meds(request, record):
    c = MedStoreConnector(request, record)
    return put_rdf(request, c)

@paramloader()
def delete_rdf_meds(request, record):
    c = MedStoreConnector(request, record)
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
    def __init__(self, request, record):
        self.record = record 
        #todo: replace with get_or_create
        try:
            self.object = smart.models.Medication.objects.get(record=self.record)
        except:
            self.object = smart.models.Medication.objects.create(record=self.record)
        
    def get(self):    
        return self.object.triples
    
    def set(self, triples):
        self.object.triples = triples
        self.object.save()
