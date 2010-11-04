"""
RDF REST API for SMArt
Josh Mandel
"""

from base import *
from smart.lib import utils
from smart.lib.utils import smart_base, rdf_get, rdf_delete, rdf_post, rdf_response
from smart.lib.utils import parse_rdf, serialize_rdf
from django.conf import settings
import RDF
import smart.models
from smart.models.rdf_store import RecordStoreConnector, PHAConnector
import re
import uuid
import urllib
from rdfobjects import *

def record_get_one_object(obj_type):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):            
            id = obj_type.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj_type.type, kwargs['external_id'])
        return rdf_get(c, obj_type.query_one("<%s>"%id.encode()))
    return to_ret


def record_get_all_objects(parent_obj, child_obj=None):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        if (child_obj == None):
            return rdf_get(c, parent_obj.query_all())
        return rdf_get(c, parent_obj.query_one("<%s%s>"%(smart_base, 
                                                         utils.trim(request.path, 2)),
                                                         restrict=child_obj.type))
    return to_ret

def record_delete_one_object(obj_type):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):
            id = obj_type.internal_id(c, kwargs['external_id'])

        return rdf_delete(c, obj_type.query_one("<%s>"%id.encode()))
    return to_ret

def record_delete_all_objects(parent_obj, child_obj=None):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        if (child_obj == None):
            return rdf_delete(c, parent_obj.query_all())
        return rdf_delete(c, parent_obj.query_one("<%s%s>"%(smart_base, 
                                                         utils.trim(request.path, 2)),
                                                         restrict=child_obj.type))
    return to_ret

def record_post_objects(obj=None, parent_obj=None):
    def to_ret(request,  record_id, **kwargs):
        path = utils.smart_path(request)
        g = parse_rdf(request.raw_post_data)            
        for new_node in obj.generate_uris(g, path):
            if parent_obj != None:
                parent = RDF.Node(uri_string=utils.smart_parent(path))
                g.append(RDF.Statement(
                    subject=parent, 
                    predicate=obj.type, 
                    object=new_node))
                    
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        return rdf_post(c, g)    
    return to_ret


def record_put_one_object(obj, parent_obj=None):
    # An idempotent PUT requires:  
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    #  5.  POST the (new) thing to the store
    def ret(request, record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        g = parse_rdf(request.raw_post_data)    

        chain_of_ids = re.findall("external_id/([^/]+)", request.path)
        external_id = chain_of_ids[-1]
        
        path = utils.smart_external_path(request)    
        if (len(chain_of_ids) > 1):
            parent_external_id = chain_of_ids[-2]
            parent_id = parent_obj.internal_id(c, parent_external_id)
            assert (parent_id != None), "No parent exists with external_id %s"%parent_external_id
            path = parent_id + parent_obj.path_to(obj)
            
        obj.ensure_only_one_put(g)
    
        new_nodes = obj.generate_uris(g, path)
        assert len(new_nodes) == 1, "Expected exactly one new node in %s ; %s"%(new_nodes, request.raw_post_data)

        g.append(RDF.Statement(
                subject=new_nodes[0], 
                predicate=RDF.Node(uri_string='http://smartplatforms.org/external_id'), 
                object=RDF.Node(literal=external_id.encode())))

        if parent_obj != None:
            parent = RDF.Node(uri_string=parent_id)
            
            g.append(RDF.Statement(
                subject=parent, 
                predicate=obj.type, 
                object=new_nodes[0]))
    
        id = obj.internal_id(c, external_id)  
        if (id):
            rdf_delete(c, obj.query_one("<%s>"%(id)), save=False)
        return rdf_post(c, g)

    return ret

record_med_get =          record_get_one_object(med)
record_med_delete =       record_delete_one_object(med)
record_med_put =          record_put_one_object(med)

record_meds_get =         record_get_all_objects(med)
record_meds_delete =      record_delete_all_objects(med)
record_meds_post =        record_post_objects(med)

record_med_fulfillment_get =    record_get_one_object(fill)
record_med_fulfillment_delete = record_delete_one_object(fill)
record_med_fulfillment_put =    record_put_one_object(fill, med)

record_med_fulfillments_get =    record_get_all_objects(med, fill)
record_med_fulfillments_delete = record_delete_all_objects(fill)
record_med_fulfillments_post =   record_post_objects(fill, med)

record_note_get =         record_get_one_object(note)
record_note_delete =      record_delete_one_object(note)
record_note_put =         record_put_one_object(note)

record_notes_post =       record_post_objects(note)
record_notes_get =        record_get_all_objects(note)
record_notes_delete =     record_delete_all_objects(note)

record_problem_get =      record_get_one_object(problem)
record_problem_put =      record_put_one_object(problem)
record_problem_delete =   record_delete_one_object(problem)

record_problems_post =    record_post_objects(problem)
record_problems_get =     record_get_all_objects(problem)
record_problems_delete =  record_delete_all_objects(problem)

record_allergy_get =      record_get_one_object(allergy)
record_allergy_delete =   record_delete_one_object(allergy)
record_allergy_put =      record_put_one_object(allergy)

record_allergies_post =   record_post_objects(allergy)
record_allergies_get =    record_get_all_objects(allergy)
record_allergies_delete = record_delete_all_objects(allergy)

record_demographics_get = record_get_all_objects(demographic)

def record_demographics_put(request, record_id):
    record, create_p = Record.objects.get_or_create(id=record_id)
    record_demographics_put_helper(request, record)
    
def record_demographics_put_helper(request, record):
    g = parse_rdf(request.raw_post_data)    
    c = RecordStoreConnector(record)

    demographic.generate_uris(g, "http://smartplatforms.org/records/%s/demographics"%record.id)
    rdf_delete(c, demographic.query_all(), save=False)
    return rdf_post(c, g)


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
