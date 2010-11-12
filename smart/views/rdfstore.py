"""
RDF REST API for SMArt
Josh Mandel
"""

from base import utils, PHAConnector, urllib
from smart.models.rdf_ontology import *
from smart.lib.utils import rdf_response
from rdfobjects import *

""" 
Implementation of application-specific storage
 
Each app gets a query-able RDF graph, supporting

  GET, 
  POST, 
  DELETE
  
"""
SPARQL = 'SPARQL'
def pha_storage_post (request, pha_email):
    ct = utils.get_content_type(request).lower()
    
    if (ct.find("application/rdf+xml") == -1):
        raise Exception("RDF Store only knows how to store RDF+XML content, not %s." %ct)

    g = parse_rdf(request.raw_post_data)   
    connector = PHAConnector(request) 
    for s in g:
        connector.pending_adds.append(s)
    connector.execute_transaction()
    
    return rdf_response(serialize_rdf(g))

def pha_storage_get (request, pha_email):    
    # todo: fix so apps can't get other apps' RDF.
    query = " CONSTRUCT {?s ?p ?o.} from $context WHERE {?s ?p ?o.}"
    if (SPARQL in request.GET.keys()):
        query = request.GET[SPARQL].replace("WHERE", " from $context WHERE ")

    connector = PHAConnector(request) 
    return rdf_get(connector, query)   

def pha_storage_delete(request, pha_email):
    query =  urllib.unquote_plus(request.raw_post_data[7:]).encode()      
    query = query.replace("WHERE", " from $context WHERE ")
    connector = PHAConnector(request)
    return rdf_delete(connector, query)
