from smart.models.rdf_store import *
from smart.models.records import *
from smart.lib.utils import *
import re

def record_get_object(request, record_id, obj,  **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        
        return rdf_get(c, obj.query_one("<%s>"%id.encode()))

    return to_ret(request, record_id, **kwargs)

def record_delete_object(request,  record_id, obj, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):            
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        return rdf_delete(c, obj.query_one("<%s>"%id.encode()))
    
    return to_ret(request, record_id, **kwargs)

def record_get_all_objects(request, record_id, obj,  parent_obj=None, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        return rdf_get(c, obj.query_all())

    return to_ret(request, record_id, **kwargs)

def record_delete_all_objects(request, record_id, obj,  parent_obj=None, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        return rdf_delete(c, obj.query_all())

    return to_ret(request, record_id, **kwargs)

def record_post_objects(request, record_id, obj, above_obj=None, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        path = smart_path(request)
        g = parse_rdf(request.raw_post_data)            
        new_uris = obj.generate_uris(g, path)

        if (above_obj != None):
            print "adding to an above!"
            for new_node in new_uris:
                above_node = RDF.Node(uri_string=smart_parent(path))
                pred = above_obj.predicate_for_child(obj)
                assert pred != None, "Can't derive the predicate for adding child %s to %s."%(obj.type, above_obj.type)
                g.append(RDF.Statement(
                         subject=above_node, 
                         predicate=RDF.Node(uri_string=pred), 
                         object=new_node))

        c = RecordStoreConnector(Record.objects.get(id=record_id))
        return rdf_post(c, g)    

    return to_ret(request, record_id, **kwargs)

def record_put_object(request, record_id, obj, parent_obj=None, **kwargs):
    # An idempotent PUT requires:  
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    #  5.  POST the (new) thing to the store
   raise NotImplementedError("Record PUT is not implemented.")
