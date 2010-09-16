"""
RDF Store for PHAs

Josh Mandel

"""

from base import *
from smart.lib import utils
from django.http import HttpResponseBadRequest
from django.conf import settings
import RDF
from StringIO import StringIO
import smart.models
from smart.models.rdf_store import RecordStoreConnector, PHAConnector
from smart.lib.utils import url_request, parse_rdf, serialize_rdf, bound_graph, strip_ns, x_domain
from string import Template
import re
import uuid
import httplib, urllib, urllib2

SPARQL = 'SPARQL'
smart_base = "http://smartplatforms.org"

def record_save_graph(record, g):
    c = RecordStoreConnector(record)
    c.set_graph( g )

def rdf_response(s):
    return x_domain(HttpResponse(s, mimetype="application/rdf+xml"))

@paramloader()
def record_sparql(request, record):
    c = RecordStoreConnector(record)
    res = c.sparql(request.GET['q'].encode())
    return rdf_response(res)

def sp_query(s, p):
    return """
    CONSTRUCT {?s ?p ?o.}
    FROM $context
    WHERE {
        ?s ?p ?o.
        FILTER (?s=<%s> &&  ?p=<%s>)
    }
    """% (str(s.uri), str(p.uri))
    

def recursive_query(root_subject, root_predicate, root_object, child_levels):

    base_query = """
    BASE <http://smartplatforms.org/>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    CONSTRUCT {?s ?p ?o.}
    FROM $context
    WHERE {
      $insertion_point 
    }
    """
    
    level_query = """
      {
           ${level_0_subject} %s %s.
           $insertion_point 
           ?s ?p ?o.
      }
    """ % (root_predicate, root_object)
    
    one_level = """
           ${l} ${l_pred} ?${l_next}."""

    
    level_queries = []
    for i in child_levels:
        if not child_levels[i]:
            child_levels[i] = ['any_type']            
        for level in child_levels[i]:
            this_level_insertion = ""
            for j in xrange(i):
                this_level_insertion += Template(one_level).substitute(
                            l= (j==0 and root_subject) or ("?level_%s_subject"%str(j)),
                            l_pred= "?level_%s_predicate"%str(j     ),
                            l_next=(j == i-1 and "s" or "level_%s_subject"%str(j+1)))
            if level != 'any_type':
                this_level_insertion += "\n ?s rdf:type %s."%level
            if (i == 0 and root_subject):
                this_level_insertion = "\n   FILTER (?s=%s) \n"%(root_subject)
            level_queries.append(Template(level_query).substitute(level_0_subject= root_subject or (i==0 and  "?s" or "?level_0_subject"), insertion_point = this_level_insertion))
            
    return Template(base_query).substitute(context="$context", insertion_point=" UNION ".join(level_queries))

def remap_node(model, old_node, new_node):
    for s in model.find_statements(RDF.Statement(old_node, None, None)):
        del model[s]
        model.append(RDF.Statement(new_node, s.predicate, s.object))
    for s in model.find_statements(RDF.Statement(None, None, old_node)):
        del model[s]
        model.append(RDF.Statement(s.subject, s.predicate, new_node))            
    return

def internal_id(record_connector, external_id, type):
    id_graph = parse_rdf(record_connector.sparql("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        CONSTRUCT {?s <http://smartplatforms.org/external_id> "%s".}
        FROM $context
        WHERE {?s <http://smartplatforms.org/external_id> "%s".
               ?s rdf:type %s.
              }
    """%(external_id, external_id, type)))
    
    l = list(id_graph)
    if len(l) > 1:
        raise Exception( "MORE THAN ONE ENTITY WITH EXTERNAL ID %s : %s"%(external_id, ", ".join([str(x.subject) for x in l])))

    try:
        s =  l[0].subject
        return str(s.uri).encode()   
    except: 
        return None
    

def generate_uris(g, type, uri_template):
    
    type = re.search("<(.*)>", type).group(1)
        
    qs = RDF.Statement(subject=None, 
                       predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                       object=RDF.Node(uri_string=type))
    
    def find_parent(child):
        pqs = RDF.Statement(subject=None, 
                            predicate=None, 
                            object=child)
        
        found=False
        for s in g.find_statements(pqs):
            if (found): raise Exception("Found >1 parent for ", child)
            found = s.subject.uri
        return found

    
    node_map = {}
    for s in g.find_statements(qs):
        if s.subject not in node_map:
            potential_parent =  find_parent(s.subject)
            uri_string = Template(uri_template).substitute(
                                          parent_id=potential_parent,
                                          new_id=str(uuid.uuid4())
                                          ).encode()
            node_map[s.subject] = RDF.Node(uri_string=uri_string)
    
    for (old_node, new_node) in node_map.iteritems():
        remap_node(g, old_node, new_node)
    return node_map.values()

def rdf_get(record_connector, query):
    res = record_connector.sparql(query)    
    return rdf_response(res)

def rdf_delete(record_connector, query, save=True): 
    to_delete = parse_rdf(record_connector.sparql(query))
    deleted = bound_graph()

    for r in to_delete:
       deleted.append(r)
       record_connector.pending_removes.append(r)
       
    
    if (save): record_connector.execute_transaction()
       
    return rdf_response(serialize_rdf(deleted))

def rdf_post(record_connector, new_g):
    for s in new_g:
        record_connector.pending_adds.append(s)

    record_connector.execute_transaction()
    return rdf_response(serialize_rdf(new_g))

def rdf_ensure_valid_put(g, type, uri_string):
    qs = RDF.Statement(subject=None, 
                   predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                   object=None)
    
    typed_object_count = 0
    errors = []
    for s in g.find_statements(qs):
        typed_object_count += 1
        errors.append(str(s.object))
    assert typed_object_count == 1, "You must PUT exactly one typed resource at a time; you tried putting %s: %s"%(typed_object_count, ", ".join(errors))
    
    new_nodes = generate_uris(g, type, uri_string) 
    assert len(new_nodes) == 1, "Expected exactly one typed resource with type %s"%type
  
    return new_nodes
    
def rdf_put(record_connector, graph, new_nodes, external_id, delete_query):
    graph.append(RDF.Statement(
            subject=new_nodes[0], 
            predicate=RDF.Node(uri_string='http://smartplatforms.org/external_id'), 
            object=RDF.Node(literal=external_id.encode())))

    rdf_delete(record_connector, delete_query, save=False)
    return rdf_post(record_connector, graph)


"""
MEDS 
"""
def record_meds_query(root_subject=None):
    q = recursive_query(root_subject=root_subject,
                                root_predicate="rdf:type",
                                root_object="<http://smartplatforms.org/medication>",
                                child_levels= {0: ['any_type'],
                                               1: ["<http://smartplatforms.org/fulfillment>",
                                                   "<http://smartplatforms.org/prescription>"]
                                               })
    return q

@paramloader()
def record_meds_get(request, record):
    return rdf_get(RecordStoreConnector(record), record_meds_query())

@paramloader()
def record_meds_delete(request, record):
    return rdf_delete(RecordStoreConnector(record), record_meds_query())

@paramloader()
def record_meds_post(request, record):
    
    g = parse_rdf(request.raw_post_data)
    utils.log("before sub: %s"%serialize_rdf(g))
    generate_uris(g, 
                  "<http://smartplatforms.org/medication>", 
                  "%s/records/%s/medications/${new_id}" % (smart_base, record.id))
    
    generate_uris(g,
                  "<http://smartplatforms.org/fulfillment>", 
                  "${parent_id}/fulfillments/${new_id}")
    
    generate_uris(g,
                  "<http://smartplatforms.org/prescription>", 
                  "${parent_id}/prescriptions/${new_id}")
    
    utils.log("after sub: %s"%serialize_rdf(g))
    return rdf_post(RecordStoreConnector(record), g)


"""
ONE MED 
"""
def record_med_query(root_subject):
    return record_meds_query(root_subject)


@paramloader()
def record_med_get(request, record, med_id):
    return rdf_get(RecordStoreConnector(record), record_med_query("<%s%s>"%(smart_base, request.path)))


@paramloader()
def record_med_post(request, record, med_id):
    c = RecordStoreConnector(record)    
    g = parse_rdf(request.raw_post_data)
    med_node = RDF.Node(uri_string="%s/records/%s/medications/%s" % (smart_base, record.id.encode(), med_id.encode()))
   
    for s in g:
        if (s.subject != med_node):
            raise Exception("Can't post data to %s where the subject is %s" %  (str(med_node), str(s.subject)))
        rdf_delete(c, sp_query(s.subject, s.predicate))
    
    return rdf_post(c, g)

@paramloader()
def record_med_delete(request, record, med_id):
    return rdf_delete(RecordStoreConnector(record), record_med_query("<%s%s>"%(smart_base,request.path)))

@paramloader()
def record_med_delete_external(request, record, external_id):
    c = RecordStoreConnector(record)
    id = internal_id(c, external_id, "<http://smartplatforms.org/medication>")
    return rdf_delete(c, record_med_query("<%s>"%(id)))

@paramloader()
def record_med_get_external(request, record, external_id):
    c = RecordStoreConnector(record)
    id = internal_id(c, external_id, "<http://smartplatforms.org/medication>")
    return rdf_get(c, record_med_query("<%s>"%(id)))


@paramloader()
def record_med_put(request, record, external_id):
    g = parse_rdf(request.raw_post_data)    
    c = RecordStoreConnector(record)
    q = record_med_query("<%s>"%internal_id(c, external_id, "<http://smartplatforms.org/medication>"))
    
    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/medication>",
                          "%s/records/%s/medications/${new_id}" % (smart_base, record.id))

    return rdf_put(c, g, new_nodes, external_id, q)    

"""
FULFILLMENTS 
"""
def record_med_fulfillments_query(root_subject):
    q = recursive_query(root_subject=root_subject,
                                root_predicate="rdf:type",
                                root_object="<http://smartplatforms.org/medication>",
                                child_levels= {
                                               1: ["<http://smartplatforms.org/fulfillment>"]
                                               })
    return q

@paramloader()
def record_med_fulfillments_get(request, record, med_id):
    c = RecordStoreConnector(record)
        
    return rdf_get(c, record_med_fulfillments_query("<%s%s>"%(smart_base, utils.trim(request.path, 2))))

@paramloader()
def record_med_fulfillments_delete(request, record, med_id):
    c = RecordStoreConnector(record)
    return rdf_delete(c, record_med_fulfillments_query("<%s%s>"%(smart_base,utils.trim(request.path, 2))))

@paramloader()
def record_med_fulfillments_post(request, record, med_id):
    g = parse_rdf(request.raw_post_data)
        
    new_nodes = generate_uris(g,
                  "<http://smartplatforms.org/fulfillment>", 
                  "%s/records/%s/medications/%s/fulfillments/${new_id}" % (smart_base, record.id, med_id))    
    
    for n in new_nodes:
        parent_med = "%s%s"%(smart_base,utils.trim(request.path, 2))
        g.append(RDF.Statement(
                subject=RDF.Node(uri_string=parent_med), 
                predicate=RDF.Node(uri_string='http://smartplatforms.org/fulfillment'), 
                object=n))
        
        
    c = RecordStoreConnector(record)
    
    return rdf_post(c, g)


"""
ONE FULFILLMENT 
"""
def record_med_fulfillment_query(root_subject):
    q = recursive_query(root_subject=root_subject,
                                root_predicate="rdf:type",
                                root_object="<http://smartplatforms.org/fulfillment>",
                                child_levels= {0: ["any_type"]})
    return q


@paramloader()
def record_med_fulfillment_get(request, record, med_id, fill_id):
    c = RecordStoreConnector(record)
    
    return rdf_get(c, record_med_fulfillment_query("<%s%s>"%(smart_base, request.path)))

@paramloader()
def record_med_fulfillment_delete(request, record, med_id, fill_id):
    c = RecordStoreConnector(record)
    
    return rdf_delete(c, record_med_fulfillment_query("<%s%s>"%(smart_base,request.path)))

@paramloader()
def record_med_fulfillment_get_external(request, record, external_med_id, external_fill_id):
    c = RecordStoreConnector(record)
    fill_id = internal_id(c, external_fill_id, "<http://smartplatforms.org/fulfillment>")
    return rdf_get(c, record_med_fulfillment_query("<%s>"%(fill_id)))

@paramloader()
def record_med_fulfillment_delete_external(request, record, external_med_id, external_fill_id):
    c = RecordStoreConnector(record)
    fill_id = internal_id(c, external_fill_id, "<http://smartplatforms.org/fulfillment>")
    return rdf_delete(c, record_med_fulfillment_query("<%s>"%(fill_id)))

def record_med_fulfillment_put_helper(request, c, med_id, external_fill_id):
    g = parse_rdf(request.raw_post_data)
    fill_id=internal_id(c, external_fill_id, "<http://smartplatforms.org/fulfillment>")
    q = record_med_fulfillment_query("<%s>"%fill_id)

    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/fulfillment>",
                         "%s/fulfillments/${new_id}" % (med_id))

    # add the parent (med_ --> child (fulfillment) links, which aren't supplied by the app.
    for n in new_nodes:
        g.append(RDF.Statement(
                subject=RDF.Node(uri_string=med_id),
                predicate=RDF.Node(uri_string='http://smartplatforms.org/fulfillment'), 
                object=n))
        
    return rdf_put(c, g, new_nodes, external_fill_id, q)    

@paramloader()
def record_med_fulfillment_put_external(request, record, external_med_id, external_fill_id):
    c = RecordStoreConnector(record)
    med_id = internal_id(c, external_med_id, "<http://smartplatforms.org/medication>")
    return record_med_fulfillment_put_helper(request, c, med_id, external_fill_id)


"""
PROBLEMS 
"""
def record_problems_query(root_subject=None):
    q = recursive_query(root_subject=root_subject,
                                root_predicate="rdf:type",
                                root_object="<http://smartplatforms.org/problem>",
                                child_levels= {0: ['any_type']})
    return q

@paramloader()
def record_problems_get(request, record):
    c = RecordStoreConnector(record)
    return rdf_get(c, record_problems_query())

@paramloader()
def record_problems_delete(request, record):
    c = RecordStoreConnector(record)
    return rdf_delete(c, record_problems_query())


@paramloader()
def record_problems_post(request, record):
    g = parse_rdf(request.raw_post_data)
    generate_uris(g, 
                  "<http://smartplatforms.org/problem>", 
                  "%s/records/%s/problems/${new_id}" % (smart_base,record.id))
    c = RecordStoreConnector(record)    
    return rdf_post(c, g)


"""
ONE PROBLEM 
"""
def record_problem_query(root_subject):
    return record_problems_query(root_subject)

@paramloader()
def record_problem_get(request, record, problem_id):
    c = RecordStoreConnector(record)
    return rdf_get(c, record_problem_query("<%s%s>"%(smart_base,request.path)))

@paramloader()
def record_problem_get_external(request, record, external_id):
    c = RecordStoreConnector(record)
    id = internal_id(c, external_id, "<http://smartplatforms.org/problem>")
    return rdf_get(c, record_problem_query("<%s>"%(id)))

@paramloader()
def record_problem_delete_external(request, record, external_id):
    c = RecordStoreConnector(record)
    id = internal_id(c, external_id, "<http://smartplatforms.org/problem>")
    return rdf_delete(c, record_problem_query("<%s>"%(id)))

@paramloader()
def record_problem_delete(request, record, problem_id):
    c = RecordStoreConnector(record)
    return rdf_delete(c, record_problems_query("<%s%s>"%(smart_base,request.path)))

@paramloader()
def record_problem_put(request, record, external_id):
    g = parse_rdf(request.raw_post_data)
    c = RecordStoreConnector(record)        
    q = record_problems_query("<%s>"%internal_id(c, external_id, "<http://smartplatforms.org/problem>"))

    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/problem>",
                         "%s/records/%s/problems/${new_id}" % (smart_base, record.id))
    return rdf_put(c, g, new_nodes, external_id, q)    


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

