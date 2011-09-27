from smart.models.rdf_store import *
from smart.models.records import *
from smart.lib.utils import *
import re
import datetime
from smart.client.common.rdf_ontology import sp, SMART_Class
from smart.models.mongo import key_to_mongo, records_db, key_from_mongo, RDFifier, JSONifier

def mongo_match(t, record_uri, target_uris=None):
    ret = {}
    
    if t.uri != sp.MedicalRecord:
        ret[key_to_mongo(sp.belongsTo)+".@iri"] =  record_uri

    if target_uris:
        ret["@subject"] = {"$in":list(target_uris)}
    print "MATCHIGN", ret
    return ret

def find_statement_links(json_structure, matches=None):
    if matches==None: matches = {}

    if isinstance(json_structure, str) or isinstance(json_structure, unicode):
        return matches

    if isinstance(json_structure, list):
        for sub_js in json_structure:
            find_statement_links(sub_js, matches)
        return matches

    if isinstance(json_structure, dict):
        if not "@type" in json_structure: return matches

        types = [SMART_Class[t] for t in json_structure["@type"]]
        properties = [(p.to_class, key_to_mongo(p.uri)) 
                      for t in types 
                      for p in t.object_properties 
                      if p.to_class.is_statement]

        for t, p in properties:
            try:
                targets = json_structure[p]
                if not isinstance(targets, list):
                    targets = [targets]                
                s = matches.setdefault(t, set())
                matches[t] = s.union([x["@iri"] for x in targets])
            except KeyError: pass

        for k,v in json_structure.iteritems():
            if k.startswith("@"): continue
            find_statement_links(v, matches) 

    return matches

def record_get_object(request, record_id, obj,  **kwargs):
    element_uri = get_element_uri(request)
    return record_get_all_objects(request, record_id, obj, restrict_to_element=element_uri)

def record_delete_object(request,  record_id, obj, **kwargs):
    element_uri = get_element_uri(request)
    return record_delete_all_objects(request, record_id, obj, restrict_to_element=element_uri)

def record_get_all_objects(request, record_id, obj, **kwargs):
    g = record_get_all_helper(request, record_id, obj, **kwargs)
    return rdf_response(g.serialize())

def record_get_all_helper(request, record_id, obj, **kwargs):
    record_uri = get_record_uri(record_id)
    restrict_to_element = get_restriction_element(**kwargs)

    if hasattr(kwargs, 'follow'):
        follow = kwargs['follow']
    else:
        follow = True

    results = []
    ts =  datetime.datetime.now()
    # Find results in patient record matching the given type
    for r in  records_db[obj.uri].find(mongo_match(obj,
                                                   record_uri, 
                                                   restrict_to_element)):
        results.append(r)

    tf = datetime.datetime.now() - ts    
    print "Main element fetched", tf

    # Resolve links one level deeper, e.g. finding fills for a med,
    # or encounters for a set of vital signs.
    if follow and len(results)==1:
        for t,v in find_statement_links(results[0]).iteritems():
            for result in records_db[t.uri].find(mongo_match(t,
                                                         record_uri, 
                                                         v)):
                results.append(result)

    tf = datetime.datetime.now() - ts    
    print "Links fetched", tf

    g = RDFifier(results).graph
    tf = datetime.datetime.now() - ts    
    print "Rehydrated RDF graph", tf
    return g


def record_delete_all_objects(request, record_id, obj, **kwargs):
    to_delete_g = record_get_all_helper(request, record_id, obj, follow=False, **kwargs)
    print "delgraph", to_delete_g

    record_uri = get_record_uri(record_id)
    restrict_to_element = get_restriction_element(**kwargs)

    # Find results in patient record matching the given type
    print "REMOVING", obj.uri, record_uri, restrict_to_element
    records_db[obj.uri].remove(mongo_match(obj,
                                           record_uri, 
                                           restrict_to_element))

    return rdf_response(to_delete_g.serialize())

def record_post_objects(request, record_id, obj,  **kwargs):
    record_uri = get_record_uri(record_id)
    path = smart_path(request.path)
    g = parse_rdf(request.raw_post_data)

    var_bindings= { 'record_id': record_id }
    obj.prepare_graph(g, None, var_bindings)

    b = JSONifier(g)
    skipped = {}

    def ensure_exists(t, skipped_v):
        for k, v in skipped_v.iteritems():
            if k[0]=='@': continue
            
            assert isinstance(v, list), "%s vs. %s"%(k,v)# Allow links from external object only in list properties

        exists_q = mongo_match(t, record_uri, [skipped_v['@subject']])
        exists = records_db[t.uri].find_one(exists_q)
        assert exists, "New object needs %s %s"%(t.uri,  exists_q)
        return

    for k, v in b.statement_elements.iteritems():
        if str(obj.uri) not in v['@type']:
            t = SMART_Class[v['@type'][0]]
            ensure_exists(t, v)
            skipped.setdefault(t, []).append(v)
            continue

        records_db[str(obj.uri)].insert(v)

    for t, skipped_vals in skipped.iteritems():
        for skipped_v in skipped_vals:
            exists_q = mongo_match(t, record_uri, [skipped_v['@subject']])
            updates = {}
            for k, v in skipped_v.iteritems():
                if k[0]=='@': continue
                updates[k] = {k: v}
            print "UPDATING", exists_q, updates
            records_db[t.uri].update(exists_q, {'$pushAll': updates})        
        
    return rdf_response(g.serialize())

def record_put_object(request, record_id, obj, **kwargs):
    # An idempotent PUT requires:  
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    record_delete_object(request,  record_id, obj, **kwargs)

    #  5.  POST the (new) thing to the store
    record_post_objects(request,  record_id, obj, **kwargs)


def get_record_uri(record_id):
    return smart_path("/records/"+record_id)

def get_element_uri(request):
    return smart_path(request.path)

def get_restriction_element(**kwargs):
    try: restrict_to_element = [kwargs['restrict_to_element']]
    except: restrict_to_element = None
    return restrict_to_element

