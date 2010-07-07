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



SPARQL = 'SPARQL'

def parse_rdf(string, model,context="none"):
#    print "PSIM: STRING=", string
#    print "PSIM: MODEL = ", model 
    parser = RDF.Parser()
#    print "Parsing into model: ", string.encode()
    try:
        parser.parse_string_into_model(model, string.encode(), context)
        
    except  RDF.RedlandError: pass
        
"""Serializes a Redland model or CONSTRUCT query result with namespaces pre-set"""
def serialize_rdf(model):
    serializer = bound_serializer()

    try: return serializer.serialize_model_to_string(model)
    except AttributeError:
      try:
          tmpmodel = RDF.Model()
          tmpmodel.add_statements(model.as_stream())
          return serializer.serialize_model_to_string(tmpmodel)
      except AttributeError:
          return '<?xml version="1.0" encoding="UTF-8"?>'

def default_ns():
   d = {}
   d['dc'] = RDF.NS('http://purl.org/dc/elements/1.1/')
   d['dcterms'] = RDF.NS('http://purl.org/rss/1.0/modules/dcterms/')
   d['med'] = RDF.NS('http://smartplatforms.org/med#')
   d['rdf'] = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
   d['rxn'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/')
   d['rxcui'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXCUI/')
   d['rxaui'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXAUI/')
   d['rxatn'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXATN#')
   d['rxrel'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/REL#')
   d['ccr'] = RDF.NS('urn:astm-org:CCR')
   return d

def bind_ns(serializer, ns=default_ns()):
    for k in ns.keys():
        v = ns[k]
        print "bindng: ", k, v._prefix
        serializer.set_namespace(k, RDF.Uri(v._prefix))

def bound_graph():
    return RDF.Model()

def bound_serializer():
    s = RDF.RDFXMLSerializer()
    bind_ns(s)
    return s 

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
