from smart.models.rdf_store import *
from smart.models.records import *
from smart.lib.utils import *
import re

def record_get_object(request, record_id, obj_type,  **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        
        return rdf_get(c, obj.query_one("<%s>"%id.encode()))

    obj = kwargs['ontology'][obj_type]
    return to_ret(request, record_id, **kwargs)

def record_delete_object(request,  record_id, obj_type, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):            
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        return rdf_delete(c, obj.query_one("<%s>"%id.encode()))
    
    obj = kwargs['ontology'][obj_type]
    return to_ret(request, record_id, **kwargs)

def record_get_all_objects(request, record_id, obj_type,  parent_obj_type=None, **kwargs):
    restrict_type = None
    if (parent_obj_type != None):
        restrict_type = obj_type
        obj_type = parent_obj_type

    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        if (restrict == None):
            return rdf_get(c, obj.query_all())
        return rdf_get(c, obj.query_one("<%s%s>"%(smart_base, 
                                                         trim(request.path, 2)),
                                                         restrict=restrict.type))

    obj = kwargs['ontology'][obj_type]
    restrict = kwargs['ontology'][restrict_type]
    return to_ret(request, record_id, **kwargs)

def record_delete_all_objects(request, record_id, obj_type,  parent_obj_type=None, **kwargs):
    restrict_type = None
    if (parent_obj_type != None):
        restrict_type = obj_type
        obj_type = parent_obj_type

    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        if (restrict == None):
            return rdf_delete(c, obj.query_all())
        return rdf_delete(c, obj.query_one("<%s%s>"%(smart_base, 
                                                         trim(request.path, 2)),
                                                         restrict=restrict.type))

    obj = kwargs['ontology'][obj_type]
    restrict = kwargs['ontology'][restrict_type]
    return to_ret(request, record_id, **kwargs)

def record_post_objects(request, record_id, obj_type, parent_obj_type=None, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        path = smart_path(request)
        g = parse_rdf(request.raw_post_data)            
        for new_node in obj.generate_uris(g, path):
            if parent_obj != None:
                parent = RDF.Node(uri_string=smart_parent(path))
                g.append(RDF.Statement(
                    subject=parent, 
                    predicate=obj.type_node(), 
                    object=new_node))
                    
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        return rdf_post(c, g)    

    obj = kwargs['ontology'][obj_type]
    
    parent_obj = kwargs['ontology'][parent_obj_type]
    return to_ret(request, record_id, **kwargs)

def record_put_object(request, record_id, obj_type, parent_obj_type=None, **kwargs):
    # An idempotent PUT requires:  
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    #  5.  POST the (new) thing to the store
    def to_ret(request, record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        g = parse_rdf(request.raw_post_data)    

        chain_of_ids = re.findall("external_id/([^/]+)", request.path)
        external_id = chain_of_ids[-1]
        
        path = smart_external_path(request)    
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
                predicate=obj.type_node(), 
                object=new_nodes[0]))
    
        id = obj.internal_id(c, external_id)  
        if (id):
            rdf_delete(c, obj.query_one("<%s>"%(id)), save=False)
        return rdf_post(c, g)

    obj = kwargs['ontology'][obj_type]
    parent_obj = kwargs['ontology'][parent_obj_type]
    return to_ret(request, record_id, **kwargs)
