from smart.models.rdf_store import *
from smart.models.records import *
from smart.lib.utils import *
import re

def record_get_object(request, record_id, obj,  **kwargs):
    c = RecordStoreConnector(Record.objects.get(id=record_id))
    id = smart_base + request.path                
    if ('external_id' in kwargs):
        id = obj.internal_id(c, kwargs['external_id'])
        assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
    
    return rdf_get(c, obj.query_one("<%s>"%id.encode()))

def record_delete_object(request,  record_id, obj, **kwargs):
    c = RecordStoreConnector(Record.objects.get(id=record_id))
    id = smart_base + request.path                
    if ('external_id' in kwargs):            
        id = obj.internal_id(c, kwargs['external_id'])
        assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
    return rdf_delete(c, obj.query_one("<%s>"%id.encode()))

def record_get_all_objects(request, record_id, obj, above_obj=None, **kwargs):
    above_uri = None
    if (above_obj != None):
        above_uri = smart_base+trim(request.path, 2)

    c = RecordStoreConnector(Record.objects.get(id=record_id))
    return rdf_get(c, obj.query_all(above_type=above_obj, above_uri=above_uri))

def record_delete_all_objects(request, record_id, obj,  above_obj=None, **kwargs):
    above_uri = None
    if (above_obj != None):
        above_uri = smart_base+trim(request.path, 2)

    
    c = RecordStoreConnector(Record.objects.get(id=record_id))
    return rdf_delete(c, obj.query_all(above_type=above_obj, above_uri=above_uri))

def record_post_objects(request, record_id, obj, above_obj=None, **kwargs):
    path = smart_path(request)
    g = parse_rdf(request.raw_post_data)
    var_bindings = obj.path_var_bindings(smart_path(request))
    new_uris = obj.generate_uris(g, var_bindings)

    if (above_obj != None):
        pred = above_obj.predicate_for_child(obj)
        assert pred != None, "Can't derive the predicate for adding %s below %s."%(obj.type, above_obj.type)
        for new_node in new_uris:
            above_node = RDF.Node(uri_string=smart_parent(path))
            g.append(RDF.Statement(
                     subject=above_node, 
                     predicate=pred, 
                     object=new_node))

    c = RecordStoreConnector(Record.objects.get(id=record_id))
    return rdf_post(c, g)    

def record_put_object(request, record_id, obj, above_obj=None, **kwargs):
    # An idempotent PUT requires:  
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    #  5.  POST the (new) thing to the store
    c = RecordStoreConnector(Record.objects.get(id=record_id))
    g = parse_rdf(request.raw_post_data)    

    chain_of_ids = re.findall("external_id/([^/]+)", request.path)
    external_id = chain_of_ids[-1]
    above_internal_id=None
    
    if (len(chain_of_ids) > 1):
        above_external_id = chain_of_ids[-2]
        above_internal_id = above_obj.internal_id(c, above_external_id)
        assert (above_internal_id != None), "No containing object exists with external_id %s"%above_external_id

    obj.ensure_only_one_put(g)
    var_bindings = obj.path_var_bindings(smart_path(request))
    new_nodes = obj.generate_uris(g, var_bindings)
    
    assert len(new_nodes) == 1, "Expected exactly one new node in %s ; %s"%(new_nodes, request.raw_post_data)
    new_node = new_nodes[0]
    
    g.append(RDF.Statement(
            subject=new_node, 
            predicate=RDF.Node(uri_string='http://smartplatforms.org/external_id'), 
            object=RDF.Node(literal=external_id.encode())))

    if above_internal_id != None:
#        print "Adding under an above", above_internal_id, above_obj.predicate_for_child(obj), new_node
        g.append(RDF.Statement(
            subject=RDF.Node(uri_string=above_internal_id), 
            predicate=RDF.Node(uri_string=above_obj.predicate_for_child(obj)), 
            object=new_node))

    id = obj.internal_id(c, external_id)  
    if (id):
        rdf_delete(c, obj.query_one("<%s>"%(id)), save=False)
    return rdf_post(c, g)

