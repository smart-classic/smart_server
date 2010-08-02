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
from smart.lib.utils import parse_rdf, serialize_rdf, bound_graph, strip_ns, x_domain
from string import Template
import re
import uuid

SPARQL = 'SPARQL'
smart_base = "http://smartplatforms.org"

def record_fetch_graph(record):
    c = RecordStoreConnector(record)
    g = parse_rdf(c.get())
    return g


def record_save_graph(record, g):
    c = RecordStoreConnector(record)
    triples = serialize_rdf(g)
    c.set( triples )

def query_graph(queries, graph, serialize=True):

    g = bound_graph()
    
    for query in queries:
        query = query.encode()
#        print "QUERYING ", query
        q = RDF.SPARQLQuery(query)
        res = q.execute(graph)
        try:
            for s in res.as_stream():
                if not g.contains_statement(s):
                    g.append(s)
        except TypeError: pass

    if (not serialize):
        return g    
    return serialize_rdf(g)

def rdf_response(s):
    return x_domain(HttpResponse(s, mimetype="application/rdf+xml"))

@paramloader()
def record_sparql(request, record):
    g = record_fetch_graph(record)  
    res_string = ""
    if ('q' not in request.GET.keys()):
        res_string = triples
    else:
        res_string = query_graph(request.GET['q'].encode(), g)

    return rdf_response(res_string)

from string import Template
def recursive_query(root_subject, root_predicate, root_object, child_levels):

    base_query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    CONSTRUCT {?s ?p ?o.}
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
            
    return [Template(base_query).substitute(insertion_point=level_query) for level_query in level_queries]

def remap_node(model, old_node, new_node):
    for s in model.find_statements(RDF.Statement(old_node, None, None)):
        del model[s]
        model.append(RDF.Statement(new_node, s.predicate, s.object))
    for s in model.find_statements(RDF.Statement(None, None, old_node)):
        del model[s]
        model.append(RDF.Statement(s.subject, s.predicate, new_node))            
    return

def internal_id(record, external_id):
    graph = record_fetch_graph(record)
    
    qs = RDF.Statement(subject=None, 
                       predicate=RDF.Node(uri_string="http://smartplatforms.org/external_id"), 
                       object=RDF.Node(literal=external_id.encode()))
    
    child = None
    for s in graph.find_statements(qs):
        q = s.subject
        break

    return str(s.subject.uri)   
    

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
            print "found one subhect", s.subject
            potential_parent =  find_parent(s.subject)
            uri_string = Template(uri_template).substitute(
                                          parent_id=potential_parent,
                                          new_id=str(uuid.uuid4())
                                          ).encode()
#            print "made up URI: ", uri_string
            node_map[s.subject] = RDF.Node(uri_string=uri_string)
    
    mapped_external = False
    for (old_node, new_node) in node_map.iteritems():
        remap_node(g, old_node, new_node)
    print serialize_rdf(g)
    return node_map.values()

def rdf_get(record, query):
    g = record_fetch_graph(record)  
    res_string = query_graph(query, g)
#    print "RESULT ", res_string
    return rdf_response(res_string)

def rdf_delete(record, query):      
    g = record_fetch_graph(record)  
    deleted = bound_graph()

    for r in query_graph(query, g, serialize=False):
       deleted.append(r)
       g.remove_statement(r)
    
    record_save_graph(record, g)
    return rdf_response(serialize_rdf(deleted))

def rdf_post(record, new_g):
    g = record_fetch_graph(record)  

    for s in new_g:
        if not g.contains_statement(s):
            g.append(s)
    
    record_save_graph(record, g)
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
    
def rdf_put(record, graph, new_nodes, external_id, delete_query):
    
    graph.append(RDF.Statement(
            subject=new_nodes[0], 
            predicate=RDF.Node(uri_string='http://smartplatforms.org/external_id'), 
            object=RDF.Node(literal=external_id.encode())))
    

    print "PUTting ", serialize_rdf(graph)
    
    rdf_delete(record, delete_query)        
    return rdf_post(record, graph)


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
    return rdf_get(record, record_meds_query())

@paramloader()
def record_meds_delete(request, record):
    return rdf_delete(record, record_meds_query())

@paramloader()
def record_meds_post(request, record):
    g = parse_rdf(request.raw_post_data)
    generate_uris(g, 
                  "<http://smartplatforms.org/medication>", 
                  "%s/records/%s/medications/${new_id}" % (smart_base, record.id))
    
    generate_uris(g,
                  "<http://smartplatforms.org/fulfillment>", 
                  "${parent_id}/fulfillments/${new_id}")
    
    generate_uris(g,
                  "<http://smartplatforms.org/prescription>", 
                  "${parent_id}/prescriptions/${new_id}")
    
    return rdf_post(record, g)


"""
ONE MED 
"""
def record_med_query(root_subject):
    return record_meds_query(root_subject)


@paramloader()
def record_med_get(request, record, med_id):
    return rdf_get(record, record_med_query("<%s%s>"%(smart_base, request.path)))

@paramloader()
def record_med_delete(request, record, med_id):
    return rdf_delete(record, record_med_query("<%s%s>"%(smart_base,request.path)))

@paramloader()
def record_med_delete_external(request, record, external_id):
    id = internal_id(record, external_id)
    return rdf_delete(record, record_med_query("<%s>"%(id)))

@paramloader()
def record_med_get_external(request, record, external_id):
    id = internal_id(record, external_id)
    return rdf_get(record, record_med_query("<%s>"%(id)))


@paramloader()
def record_med_put(request, record, external_id):
    q = recursive_query(root_subject=None,
                                root_predicate="<http://smartplatforms.org/external_id>",
                                root_object='"%s"'%external_id,
                                child_levels= {0: ["<http://smartplatforms.org/medication>"],
                                               1: ["<http://smartplatforms.org/fulfillment>",
                                                   "<http://smartplatforms.org/prescription>"]
                                               })


    g = parse_rdf(request.raw_post_data)    

    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/medication>",
                          "%s/records/%s/medications/${new_id}" % (smart_base, record.id))
    
    return rdf_put(record, g, new_nodes, external_id, q)    



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
    return rdf_get(record, record_med_fulfillments_query("<%s%s>"%(smart_base, utils.trim(request.path, 2))))

@paramloader()
def record_med_fulfillments_delete(request, record, med_id):    
    return rdf_delete(record, record_med_fulfillments_query("<%s%s>"%(smart_base,utils.trim(request.path, 2))))

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
        
        print "POSTING ", serialize_rdf(g)
        

    return rdf_post(record, g)


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
    return rdf_get(record, record_med_fulfillment_query("<%s%s>"%(smart_base, request.path)))

@paramloader()
def record_med_fulfillment_get_external(request, record, med_id, external_id):
    id = internal_id(record, external_id)
    return rdf_get(record, record_med_fulfillment_query("<%s>"%(id)))

@paramloader()
def record_med_fulfillment_delete_external(request, record, med_id, external_id):
    id = internal_id(record, external_id)
    return rdf_delete(record, record_med_fulfillment_query("<%s>"%(id)))


# TODO: implement the delete query by first grabbing the internal ID, then running standard internal delete.
@paramloader()
def record_med_fulfillment_put(request, record, med_id, external_id):
    q = recursive_query(root_subject=None,
                                root_predicate="<http://smartplatforms.org/external_id>",
                                root_object='"%s"'%external_id,
                                child_levels= {
                                               0: ["<http://smartplatforms.org/fulfillment>"],
                                               })

    g = parse_rdf(request.raw_post_data)
    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/fulfillment>",
                         "%s/records/%s/medications/%s/fulfillments/${new_id}" % (smart_base, record.id, med_id))

    for n in new_nodes:
        parent_med = "%s%s"%(smart_base,utils.trim(request.path, 3))
        g.append(RDF.Statement(
                subject=RDF.Node(uri_string=parent_med), 
                predicate=RDF.Node(uri_string='http://smartplatforms.org/fulfillment'), 
                object=n))
    
    return rdf_put(record, g, new_nodes, external_id, q)    



@paramloader()
def record_med_fulfillment_delete(request, record, med_id, fill_id):
    return rdf_delete(record, record_med_fulfillment_query("<%s%s>"%(smart_base,request.path)))


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
    return rdf_get(record, record_problems_query())

@paramloader()
def record_problems_delete(request, record):
    return rdf_delete(record, record_problems_query())


@paramloader()
def record_problems_post(request, record):
    g = parse_rdf(request.raw_post_data)
    generate_uris(g, 
                  "<http://smartplatforms.org/problem>", 
                  "%s/records/%s/problems/${new_id}" % (smart_base,record.id))
    
    return rdf_post(record, g)


"""
ONE PROBLEM 
"""
def record_problem_query(root_subject):
    print "RPBOEM Q: ", record_problems_query(root_subject)
    return record_problems_query(root_subject)


@paramloader()
def record_problem_get(request, record, problem_id):
    return rdf_get(record, record_problem_query("<%s%s>"%(smart_base,request.path)))


@paramloader()
def record_problem_get_external(request, record, external_id):
    id = internal_id(record, external_id)
    return rdf_get(record, record_problem_query("<%s>"%(id)))

@paramloader()
def record_problem_delete_external(request, record, external_id):
    id = internal_id(record, external_id)
    return rdf_delete(record, record_problem_query("<%s>"%(id)))

@paramloader()
def record_problem_delete(request, record, problem_id):
    return rdf_delete(record, record_problems_query("<%s%s>"%(smart_base,request.path)))


@paramloader()
def record_problem_put(request, record, external_id):
    print "PUTting ", request.raw_post_data
    q = recursive_query(root_subject=None,
                                root_predicate="<http://smartplatforms.org/external_id>",
                                root_object='"%s"'%external_id,
                                child_levels= {
                                               0: ["<http://smartplatforms.org/problem>"]
                                               })
    

    g = parse_rdf(request.raw_post_data)
    new_nodes = rdf_ensure_valid_put(g, 
                         "<http://smartplatforms.org/problem>",
                         "%s/records/%s/problems/${new_id}" % (smart_base, record.id))
    
    return rdf_put(record, g, new_nodes, external_id, q)    

 
# Replace the entire store with data passed in
def post_rdf (request, connector, maintain_existing_store=False):
    ct = utils.get_content_type(request).lower()
    
    if (ct.find("application/rdf+xml") == -1):
        raise Exception("RDF Store only knows how to store RDF+XML content, not %s." %ct)
    
    print "Content-type of req: ", ct
    
    g = bound_graph()
    triples = connector.get()
    
    if (maintain_existing_store and triples != ""):
        parse_rdf(triples, g, "existing") 
        
    parse_rdf(request.raw_post_data,g, "new")
   
    triples = serialize_rdf(g)
    connector.set( triples )
    
    return x_domain(HttpResponse(triples, mimetype="application/rdf+xml"))


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
    c = MedStoreConnector(request, record)

    print "Med CCR Received:  ",request.raw_post_data

    # Reconcile blank nodes based on previously-processed data
    new_rdf = meds_as_rdf(request.raw_post_data)
    HashedMedication.conditional_create(model=new_rdf, context=record.id)

    # Add any new statements (incremental diff, additions only)
    old_rdf = utils.parse_rdf(c.get())
    utils.update_store(old_rdf, new_rdf) # copy new triples from new --> old
    old_rdf = utils.serialize_rdf(old_rdf)
    
    # Overwrite the store and send a copy of results to caller.
    c.set(old_rdf)
    return x_domain(HttpResponse(old_rdf, mimetype="application/rdf+xml"))
    
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
        
class RecordStoreConnector():
    def __init__(self, record):
        self.record = record 
        #todo: replace with get_or_create
        try:
            self.object = smart.models.RecordRDF.objects.get(record=self.record)
        except:
            self.object = smart.models.RecordRDF.objects.create(record=self.record)
        
    def get(self):    
        return self.object.triples
    
    def set(self, triples):
        self.object.triples = triples
        self.object.save()

def meds_as_rdf(raw_xml):
#    demographic_rdf_str = xslt_ccr_to_rdf(raw_xml, "ccr_to_demographic_rdf")
#    m = RDF.Model()
#    demographic_rdf = parse_rdf(demographic_rdf_str, m)
    med_rdf_str = utils.xslt_ccr_to_rdf(raw_xml, "ccr_to_med_rdf")
    g = parse_rdf(med_rdf_str)
#    rxcui_ids = RDF.SPARQLQuery("""
#                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
#                    PREFIX med: <http://smartplatforms.org/med#>
#                    SELECT ?cui_id  
#                    WHERE {
#                    ?med rdf:type med:medication .
#                    ?med med:drug ?cui_id .
#                    }""").execute(g)
#    for r in rxcui_ids: 
#        try:
#            rxcui_id = strip_ns(r['cui_id'], "http://link.informatics.stonybrook.edu/rxnorm/RXCUI/")          
#            utils.rxn_related(rxcui_id=rxcui_id, graph=g)
#        except ValueError:
#            pass
    return g
