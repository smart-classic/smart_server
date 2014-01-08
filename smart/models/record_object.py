import re
import os
import hashlib
import base64
import uuid
from django.conf import settings
from smart.common.rdf_tools.rdf_ontology import api_types, api_calls, ontology, SMART_Class
from smart.common.rdf_tools.query_builder import SMART_Querier
from rdf_rest_operations import *
from smart.common.rdf_tools.util import remap_node, parse_rdf, get_property, LookupType, BNode, Literal, URIRef, sp, rdf, default_ns, NS
from rdflib import Graph, ConjunctiveGraph, RDF
from ontology_url_patterns import CallMapper, BasicCallMapper


class RecordObject(object):
    __metaclass__ = LookupType
    known_types_dict = {}

    get_one = staticmethod(record_get_object)
    get_all = staticmethod(record_get_all_objects)
    delete_one = staticmethod(record_delete_object)
    delete_all = staticmethod(record_delete_all_objects)
    post = staticmethod(record_post_objects)
    put = staticmethod(record_put_object)

    def __init__(self, smart_type):
        self.smart_type = smart_type
        RecordObject.register_type(smart_type, self)

    @classmethod
    def __getitem__(cls, key):
        try:
            return cls.known_types_dict[key]
        except:
            try:
                return cls.known_types_dict[key.uri]
            except:
                return cls.known_types_dict[URIRef(key.encode())]

    @classmethod
    def register_type(cls, smart_type, robj):
        cls.known_types_dict[smart_type.uri] = robj

    @property
    def properties(self):
        return [x.property for x in self.smart_type.properties]

    @property
    def uri(self):
        return str(self.smart_type.uri)

    @property
    def node(self):
        return self.smart_type.uri

    @property
    def path(self):
        v = self.smart_type.base_path
        if v:
            return str(v)
        return None

    def path_var_bindings(self, request_path):
        var_names = re.findall("{(.*?)}", self.path)

        match_string = self.path
        for i, v in enumerate(var_names):
            # Force all variables to match, except the final one
            # (which can be a new GUID, substituted in on-the-fly.)
            repl = i + 1 < len(var_names) and "([^\/]+).*" or "([^\/]*?)"
            match_string = re.sub("{" + v + "}", repl, match_string)
        matches = re.search(match_string, request_path).groups()
        var_values = {}

        for i, v in enumerate(var_names):
            if matches[i] != "":
                var_values[v] = matches[i]

        return var_values

    def determine_full_path(self, var_bindings=None):
        ret = settings.SITE_URL_PREFIX + self.path
        for vname, vval in var_bindings.iteritems():
            if vval == "":
                vval = "{new_id}"
            ret = ret.replace("{" + vname + "}", vval)

        still_unbound = re.findall("{(.*?)}", ret)
        assert len(still_unbound) <= 1, "Can't match path closely enough: %s given %s -- got to %s" % (self.path, var_bindings, ret)
        if len(still_unbound) == 1:
            ret = ret.replace("{" + still_unbound[0] + "}", str(uuid.uuid4()))

        return URIRef(ret)

    def statement_type(self, g, n):
        node_type_candidates = list(g.triples((n, rdf.type, None)))
        node_type = None
        for c in node_type_candidates:
            # print '========= c is ' + str(c)
            t = SMART_Class[c[2]]
            if t.is_statement or t.uri == sp.MedicalRecord:
                assert node_type is None, "Got multiple node types for %s" % [
                    x[2] for x in node_type]
                node_type = t.uri
        return node_type

    def determine_remap_target(self, g, c, s, var_bindings):
        if type(s) != BNode:
            return None

        node_type = self.statement_type(g, s)

        if node_type is None:
            return None

        full_path = RecordObject[node_type].determine_full_path(var_bindings)
        return full_path

    def generate_uris(self, g, c, var_bindings=None):
        node_map = {}
        nodes = set(g.subjects()) | set(g.objects())
        for s in nodes:
            new_node = self.determine_remap_target(g, c, s, var_bindings)
            if new_node:
                node_map[s] = new_node

        for (old_node, new_node) in node_map.iteritems():
            remap_node(g, old_node, new_node)

        return node_map.values()

    def attach_statements_to_record(self, g, new_uris, var_bindings):
        # Attach each data element (med, problem, lab, etc), to the
        # base record URI with the sp:Statement predicate.
        recordURI = URIRef(
            smart_path("/records/%s" % var_bindings['record_id']))
        for n in new_uris:
            node_type = get_property(g, n, rdf.type)

            # Filter for top-level medical record "Statement" types
            t = ontology[node_type]
            if (not t.is_statement):
                continue
            if (not t.base_path.startswith("/records")):
                continue
            if (n == recordURI):
                continue  # don't assert that the record has itself as an element

            # There's no need to include belongsTo in a POSTed graph.
            # ... but if belongsTo is present, it must be identical
            # to the current recordURI
            existing_record = list(g.triples((n, sp.belongsTo, None)))
            if len(existing_record) > 1:
                raise Exception("Can't have multiple belongsTo statements")
            if len(existing_record) > 0 \
                and existing_record[0][2] != recordURI:
                    raise Exception("Conflicting belongsTo statements")

            g.add((n, sp.belongsTo, recordURI))
            g.add((recordURI, sp.hasStatement, n))
            g.add((recordURI, rdf.type, sp.MedicalRecord))

    def segregate_nodes(self, data, r, context=None):

        if context is None:
            context = r

        # Recursion base case:  we've already started evaluating
        # this node as a root before --> don't evaluate it again!
        if r == context and len(data.get_context(context)) > 0:
            return

        nodes_to_recurse = {}
        for s, p, o in data.triples((r, None, None)):
            data.get_context(context).add((s, p, o))

            if type(o) == Literal:
                continue

            nodes_to_recurse[o] = o
            if not self.statement_type(data, o):
                nodes_to_recurse[o] = context

        for node, context in nodes_to_recurse.iteritems():
            self.segregate_nodes(data, node, context)

        return

    def prepare_graph(self, g, c, var_bindings=None):
        new_uris = self.generate_uris(g, c, var_bindings)
        self.attach_statements_to_record(g, new_uris, var_bindings)

    def query(self, *args, **kwargs):
        ret = SMART_Querier.query(self.smart_type, *args, **kwargs)
        return ret

for t in api_types:
    RecordObject(t)


class RecordCallMapper(object):
    def __init__(self, call):
        self.call = call
        # print 'RecordCallMapper->init', self.call.target,
        # RecordObject[self.call.target]
        self.obj = RecordObject[self.call.target]

    @property
    def get(self):
        return None

    @property
    def delete(self):
        return None

    @property
    def post(self):
        return self.obj.post

    @property
    def put(self):
        return self.obj.put

    @property
    def map_score(self):
        cat = str(self.call.category)
        cardinality = str(self.call.cardinality)
        #print "considering", cat, cardinality, "vs",self.cardinality
        if cat == "record" and cardinality == self.cardinality:
            return 1
        return 0

    @property
    def arguments(self):
        r = {'obj': self.obj}
        return r

    @property
    def maps_to(self):
        m = str(self.call.http_method)

        if "GET" == m:
            return self.get
        if "PUT" == m:
            return self.put
        if "POST" == m:
            return self.post
        if  "DELETE" == m:
            return self.delete

        assert False, "Method not in GET, PUT, POST, or DELETE"


@CallMapper.register
class RecordItemsCallMapper(RecordCallMapper):
    @property
    def get(self):
        return self.obj.get_all

    @property
    def delete(self):
        return self.obj.delete_all

    cardinality = "multiple"


@CallMapper.register
class RecordItemCallMapper(RecordCallMapper):
    @property
    def get(self):
        return self.obj.get_one

    @property
    def delete(self):
        return self.obj.delete_one
    cardinality = "single"


@CallMapper.register(client_method_name="get_allergies")
def record_get_allergies(request, *args, **kwargs):
    record_id = kwargs['record_id']
    a = RecordObject["http://smartplatforms.org/terms#Allergy"]
    ae = RecordObject["http://smartplatforms.org/terms#AllergyExclusion"]

    c = RecordTripleStore(Record.objects.get(id=record_id))
    allergy_graph = c.get_objects(request.path, request.GET, a)
    exclusion_graph = c.get_objects(request.path, request.GET, ae)

    a = parse_rdf(allergy_graph)
    ae = parse_rdf(exclusion_graph)

    a += ae
    return rdf_response(serialize_rdf(a))
   
def sha256(fileName):
    """Compute sha256 hash of the specified file"""
    m = hashlib.sha256()
    try:
        fd = open(fileName,"rb")
    except IOError:
        print "Unable to open the file in readmode:", fileName
        return
    content = fd.readlines()
    fd.close()
    for eachLine in content:
        m.update(eachLine)
    return m.hexdigest()
   
def fetch_documents(request, record_id, term, multiple):
    format = "metadata" if multiple else "raw"

    try:
        format = request.GET['format']
    except:
        pass

    obj = RecordObject[term]
    c = RecordTripleStore(Record.objects.get(id=record_id))

    if multiple:
        documents_graph = c.get_objects(request.path, request.GET, obj)
    else:
        item_id = URIRef(smart_path(request.path))
        documents_graph = c.get_objects(request.path, request.GET, obj, [item_id])

    rdf = parse_rdf(documents_graph)

    q = """
           PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
           PREFIX sp:<http://smartplatforms.org/terms#>
           SELECT ?s
           WHERE {
               ?s rdf:type <%s> .
           }
        """ % term

    bindings = rdf.query(q)

    if len(bindings) == 0:
        g = ConjunctiveGraph()
        return rdf_response(serialize_rdf(g))
    
    g = None

    for d in bindings:
        g2 = parse_rdf(c.get_contexts(d))
        
        q = """
           PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
           PREFIX sp:<http://smartplatforms.org/terms#>
           PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
           PREFIX dcterms:<http://purl.org/dc/terms/>
           SELECT ?d ?fn ?ct
           WHERE {
               ?d rdf:type <%s> .
               ?d sp:fileName ?fn .
               ?d dcterms:format ?f .
               ?f rdf:type dcterms:MediaTypeOrExtent .
               ?f rdfs:label ?ct .
           }
        """ % term
        
        res = g2.query(q)
        uri = [str(r[0]) for r in res][0]
        filename = [str(r[1]) for r in res][0]
        content_type = [str(r[2]) for r in res][0]
        path = settings.BASE_DOCUMENTS_PATH + "/" + record_id + "/" + filename
        
        if (not multiple and format == "raw") or term == str(NS['sp']['Photograph']):
            # Return raw content
            f = open(path, 'rb')
            file_content = f.read()
            f.close()
            return x_domain(HttpResponse(file_content, mimetype=content_type))
            
        hash = sha256(path)
        file_size = os.path.getsize(path)
        
        SP = NS['sp']
        
        vNode = BNode()
        g2.add((vNode,RDF.type,SP['ValueAndUnit']))
        g2.add((vNode,SP['value'],Literal(file_size)))
        g2.add((vNode,SP['unit'],Literal("byte")))
        
        hNode = BNode()
        g2.add((hNode,RDF.type,SP['Hash']))
        g2.add((hNode,SP['algorithm'],Literal("SHA-256")))
        g2.add((hNode,SP['value'],Literal(hash)))
        
        rNode = BNode()
        g2.add((rNode,RDF.type,SP['Resource']))
        g2.add((rNode,SP['location'],Literal(uri)))
        g2.add((rNode,SP['hash'],hNode))
        
        if format == "combined":
            ctNode = BNode()
            g2.add((ctNode,RDF.type,SP['Content']))
            
            if filename.endswith(".txt"):
                f = open(path, 'r')
                file_content = f.read()
                f.close()
                g2.add((ctNode,SP['encoding'],Literal("UTF-8")))
                g2.add((ctNode,SP['value'],Literal(file_content)))
            else:
                f = open(path, 'rb')
                encoded_file_content = base64.b64encode(f.read())
                f.close()
                g2.add((ctNode,SP['encoding'],Literal("Base64")))
                g2.add((ctNode,SP['value'],Literal(encoded_file_content)))

            g2.add((rNode,SP['content'],ctNode))
        
        cNode=URIRef(uri)
        g2.add((cNode,SP['fileSize'], vNode))
        g2.add((cNode,SP['resource'], rNode))
        
        if not g:
            g = g2
        else:
            g += g2
        
    return rdf_response(serialize_rdf(g))

def fetch_imaging_studies(request, record_id, multiple):
    term = str(NS['sp']['ImagingStudy'])

    obj = RecordObject[term]
    c = RecordTripleStore(Record.objects.get(id=record_id))

    if multiple:
        imaging_studies_graph = c.get_objects(request.path, request.GET, obj)
    else:
        item_id = URIRef(smart_path(request.path))
        imaging_studies_graph = c.get_objects(request.path, request.GET, obj, [item_id])

    return rdf_response(imaging_studies_graph)

@CallMapper.register(client_method_name="get_document")
def record_get_document(request, *args, **kwargs):
    record_id = kwargs['record_id']
    term = str(NS['sp']['Document'])
    return fetch_documents(request,record_id,term,False)
    
@CallMapper.register(client_method_name="get_documents")
def record_get_documents(request, *args, **kwargs):
    record_id = kwargs['record_id']
    term = str(NS['sp']['Document'])
    return fetch_documents(request,record_id,term,True)
    
@CallMapper.register(client_method_name="get_photograph")
def record_get_photograph(request, *args, **kwargs):
    record_id = kwargs['record_id']
    term = str(NS['sp']['Photograph'])
    return fetch_documents(request,record_id,term,True)
    
@CallMapper.register(client_method_name="get_imaging_study")
def record_get_imaging_study(request, *args, **kwargs):
    record_id = kwargs['record_id']
    return fetch_imaging_studies(request,record_id,False)
    
@CallMapper.register(client_method_name="get_imaging_studies")
def record_get_imaging_studies(request, *args, **kwargs):
    record_id = kwargs['record_id']
    return fetch_imaging_studies(request,record_id,True)
    
@CallMapper.register(client_method_name="get_medical_image")
def record_get_medical_image(request, *args, **kwargs):
    record_id = kwargs['record_id']
    term = str(NS['sp']['MedicalImage'])
    return fetch_documents(request,record_id,term,False)
    
@CallMapper.register(client_method_name="get_medical_images")
def record_get_medical_images(request, *args, **kwargs):
    record_id = kwargs['record_id']
    term = str(NS['sp']['MedicalImage'])
    return fetch_documents(request,record_id,term,True)

@CallMapper.register(client_method_name="post_alert")
def record_post_alert(request, *args, **kwargs):
    record_id = kwargs['record_id']
    r = Record.objects.get(id=record_id)
    app = request.principal.share.with_app

    RecordAlert.from_rdf(request.raw_post_data, r, app)
    return rdf_response(request.raw_post_data)
