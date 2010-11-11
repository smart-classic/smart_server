import re, RDF, os, uuid
from smart.models.rdf_store import RecordStoreConnector
from smart.models.records import Record
from smart.lib.utils import default_ns, trim, smart_base, smart_parent, smart_path, smart_external_path, rdf_get, rdf_post, rdf_delete, parse_rdf, serialize_rdf
from django.conf import settings

print "LOADING ONTOLOGY FROM SCRATCH."


NS = default_ns()
class RDFProperty(object):
    def __init__(self, predicate, object=None):
        self.predicate = predicate
        self.object = object

class RDFObject(object):
    def __init__(self, type=None, path=None):
        self.type = type
        self.path=path
        self.parent = None
        self.properties = [RDFProperty(predicate=str(NS['rdf']['type'].uri)), 
                           RDFProperty(predicate=str(NS['sp']['external_id'].uri))]
        self.children = {}
        self.post = record_post_objects
        self.put = record_put_object
        self.get_one = record_get_object
        self.get_all = record_get_all_objects
        self.delete_one = record_delete_object
        self.delete_all = record_delete_all_objects
    
    def type_node(self):
        return RDF.Node(uri_string=self.type)

    def find_parent(self, g, child):
        q_parent = RDF.Statement(subject=None, 
                            predicate=None, 
                            object=child)
        
        found=None

        for s in g.find_statements(q_parent):
            if (found): raise Exception("Found >1 parent for ", child)
            found = s.subject.uri
        return found

    def internal_id(self, record_connector, external_id):
        id_graph = parse_rdf(record_connector.sparql("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            CONSTRUCT {?s <http://smartplatforms.org/external_id> "%s".}
            FROM $context
            WHERE {?s <http://smartplatforms.org/external_id> "%s".
                   ?s rdf:type %s.
                  }
        """%(external_id, external_id, "<"+self.type+">")))
        
        l = list(id_graph)
        if len(l) > 1:
            raise Exception( "MORE THAN ONE ENTITY WITH EXTERNAL ID %s : %s"%(external_id, ", ".join([str(x.subject) for x in l])))
    
        try:
            s =  l[0].subject
            return str(s.uri).encode()   
        except: 
            return None

    
    def remap_node(self, model, old_node, new_node):
        for s in list(model.find_statements(RDF.Statement(old_node, None, None))):
            del model[s]
            model.append(RDF.Statement(new_node, s.predicate, s.object))
        for s in list(model.find_statements(RDF.Statement(None, None, old_node))):
            del model[s]
            model.append(RDF.Statement(s.subject, s.predicate, new_node))            
        return
    
    def path_to(self, child_type):
        to_strip = self.path.replace("{new_id}","")
        stripped = child_type.path.replace(to_strip, "")
        stripped = re.sub("^{.*?}", "", stripped)
        return stripped
    
    def determine_full_path(self, request_path, parent_path):
        if parent_path == None: # No parent in the supplied graph, so we just use the requess's path
                                # e.g. (/records/{rid}/medications/) to determine URIs
            if (request_path.endswith("/")): request_path += "{new_id}"
            match_string = re.sub("{.*?}", "(.*?)", self.path)
            request_path_ok = re.search(match_string, request_path).groups()
            assert(len(request_path_ok) > 0), "Expect request path to match child path"
            ret = request_path
            
        else: # a parent *was* supplied!  Just take the relative portion of this path.
            ret =  str(parent_path) + "/" + self.path.split("/")[-2] + "/{new_id}"
            
        ret = ret.replace("{new_id}", str(uuid.uuid4()))
        return ret.encode()
    
    def ensure_only_one_put(self, g):
        qs = RDF.Statement(subject=None, 
                   predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                   object=None)
    
        typed_object_count = 0
        errors = []
        for s in g.find_statements(qs):
            typed_object_count += 1
            errors.append(str(s.object))
        assert typed_object_count == 1, "You must PUT exactly one typed resource at a time; you tried putting %s: %s"%(typed_object_count, ", ".join(errors))
    
        return
    
    def generate_uris(self, g, request_path):   
        if (self.type == None): return 
    
        q_typed_nodes = RDF.Statement(subject=None, 
                                      predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                                      object=self.type_node())
    
        node_map = {}    
        for s in g.find_statements(q_typed_nodes):
            if s.subject not in node_map:
                parent_path = self.find_parent(g, s.subject)
                full_path =  self.determine_full_path(request_path, parent_path)                
                node_map[s.subject] = RDF.Node(uri_string=full_path)

        for (old_node, new_node) in node_map.iteritems():
            self.remap_node(g, old_node, new_node)
        for c in self.children.values():
            c.generate_uris(g, request_path)

        return node_map.values()

    def typed(self, level=0):
        if (self.type == None): return ""
        name = self.leveled("?s", level)
        return " " + name + " rdf:type <"+self.type+">. "
    
    def leveled(self, val, level=0):
        if level == 0: return val
        return val + "_"+str(level)
    
    def id_filter(self, id=None):
        if (id != None): return "FILTER (?s=" + id + ") "
        return ""
        
    def insertions(self, id=None, level=1, parent_clause="", restrict_to_child_types=None):
        ret = []
        
        this_level = parent_clause
        this_level += self.typed()
        
        if (id != None):
            ret.append("?s ?p ?o FILTER (?o="+id+")")
            this_level += self.id_filter(id)
            
        if (level == 1): 
            parent_clause = this_level
            parent_clause = parent_clause.replace("?s ", "?s_1 ") 
            parent_clause = parent_clause.replace("?s=", "?s_1=") 

        # If we're only interested in querying, e.g. fills that belong to a medication
        # We should still recurse down the type hierachy starting at meds -- but
        # don't actually CONSTRUCT any triples unless/until we get to a fill object.
        predicates_to_capture = [restrict_to_child_types]
        if (restrict_to_child_types == None or restrict_to_child_types == self.type):      
            restrict_to_child_types = None
            predicates_to_capture = [x.predicate for x in self.properties]  + self.children.keys() 

        this_level += "?s ?p ?o.  FILTER (" + " || ".join(["?p=<"+p+">" for p in predicates_to_capture])+")"
        ret.append(this_level)
        
        for (rel, c) in self.children.iteritems():
            next_parent_clause = parent_clause.replace("?s.", self.leveled("?s", level) + ".") + self.leveled("?s", level) + " <"+rel+"> ?s. "
            ret.extend(c.insertions(level=level+1, parent_clause=next_parent_clause, restrict_to_child_types=restrict_to_child_types)) 
            
        return ret
    
    def query_one(self, id, restrict=None):
        return self.query_all(id=id, restrict=restrict)
        
    def query_all(self, id=None,level=0, restrict=None):
        ret = """
        BASE <http://smartplatforms.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        CONSTRUCT {?s ?p ?o.}
        FROM $context
        WHERE {
           { $insertion_point } 
        }
        """

        insertions = self.insertions(id=id, restrict_to_child_types=restrict)
        ret = ret.replace("$insertion_point", " } UNION { ".join(insertions))
        
        return ret


sp  = RDF.NS("http://smartplatforms.org/")
rdf = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
owl = RDF.NS("http://www.w3.org/2002/07/owl#")
rdfs = RDF.NS("http://www.w3.org/2000/01/rdf-schema#")

class CallInfo(object):
  def __init__(self, m, c):
    self.model = m
    self.type = [str(x.subject.uri) for x in m.find_statements(RDF.Statement(None, sp['api/call'], c))][0]
    self.targets = [x.object.literal_value['string'] for x in m.find_statements(RDF.Statement(c, sp['api/target'], None))]
    self.path = [x.object.literal_value['string'] for x in m.find_statements(RDF.Statement(c, sp['api/path'], None))][0]
    self.methods = [x.object.literal_value['string'] for x in m.find_statements(RDF.Statement(c, sp['api/method'], None))]
    return

  @classmethod
  def find_all_calls(cls, m):
    def get_api_calls(m):
      q = RDF.Statement(None, sp['api/call'], None)
      r = list(m.find_statements(q))
      return r

    calls = []
    for c in get_api_calls(m):
      i = CallInfo(m, c.object)
      calls.append(i)
    return calls

  def django_param_regex(self, v):
    return "(?P<%s>[^/]+)"%v

  def getMethods(self):
    obj = ontology[self.type]
    methodHash = {"OPTIONS": "allow_options"}

    if "record_item" in self.targets and "GET" in self.methods:
      methodHash["GET"] = obj.get_one

    if "record_items"  in self.targets and "GET" in self.methods:
      methodHash["GET"] = obj.get_all

      # A cheap hack to suppor wget-driven "PUT" of 
      # resources during the initialization of the reference container.
      # (wget won't PUT and curl barfs on PUT urls ending with /) 
    if ("record_items"  in self.targets) and "PUT" in self.methods:
      methodHash["POST"] = obj.post

    if "record_item"  in self.targets and "PUT" in self.methods:
      methodHash["PUT"] = obj.put
      # A cheap hack to suppor wget-driven "PUT" of 
      # resources during the initialization of the reference container.
      # (wget won't PUT and curl barfs on PUT urls ending with /) 
      methodHash["POST"] = obj.put


    if "record_items"  in self.targets and "POST" in self.methods:
      methodHash["POST"] = obj.post

    if "record_item"  in self.targets and "DELETE" in self.methods:
      methodHash["DELETE"] =obj.delete_one

    if "record_items"  in self.targets and "DELETE" in self.methods:
      methodHash["DELETE"] = obj.get_all

    return methodHash      

  def getArguments(self):
      r = {}
      
      r['obj_type'] = self.type
      
      t = SMArtOntology()[self.type]
      if t.parent:
          r['parent_obj_type'] = t.parent.type
          
      return r
      
  # get from an absolute OWL path to a relative django-friendly URL match
  def django_path(self):
    ret = self.path
    to_replace = re.findall("{(.*?)}", ret)
    for r in to_replace:
      ret = ret.replace("{%s}"%r, self.django_param_regex(r))
    
    ret = ret.replace("http://smartplatforms.org/", "^")
    return ret+"$"



class TypeInfo(object):
  def __init__(self, m, t, calls):
    self.model = m

    supers = [x.object for x in m.find_statements(RDF.Statement(t, rdfs['subClassOf'], None))]

    properties = []
    children = {}
    for s in supers:
      props = [str(x.object.uri) for x in m.find_statements(RDF.Statement(s, owl['onProperty'], None))]
      kids = [str(x.object.uri) for x in m.find_statements(RDF.Statement(s, owl['onClass'], None))]

      if len(kids) == 0: properties.extend(props)
      else: children[props[0]] = kids[0]

    self.properties = properties
    self.children = children

    try:
        self.path = filter(lambda(x): x.type == str(t.uri)  and "base_path" in x.targets, calls)[0].path
    except: self.path = None
    
    self.type = str(t.uri)
    return


  @classmethod
  def find_all_types(cls, m):
    def get_types(m):
      q = RDF.Statement(None, rdf['type'], owl['Class'])
      r = filter(lambda x: str(x.subject.uri), list(m.find_statements(q)))
      return [v.subject for v in r]

    calls = CallInfo.find_all_calls(m)
    types = []
    by_type = {}

    for t in get_types(m):
      i = TypeInfo(m, t, calls)
      # Add type to the hash
      u = str(t.uri) 
      if u not in by_type: 
        by_type[u] = RDFObject()          

      if (i.path != None):
          by_type[u].path = i.path
          by_type[u].type = i.type
          print "typed", i.path, i.type
      else: print u + " is untyped."
      # add properties  
      for p in i.properties:
        by_type[u].properties.append(RDFProperty(p))    
      
      # add children
      for (cname, cval) in i.children.iteritems():
        if cval not in by_type:
          by_type[cval] = RDFObject()
        by_type[cval].parent = by_type[u]
        by_type[u].children[cname] = by_type[cval]

    SMArtOntology.set(by_type)
    return SMArtOntology()

class SMArtOntology(object):
  @classmethod
  def set(cls, by_type):
    cls.by_type = by_type

  def __getitem__(self, v):
    if v == None: return None
    return self.by_type[v]

def record_get_object(request,  record_id, obj_type,**kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        if ('external_id' in kwargs):
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        
        return rdf_get(c, obj.query_one("<%s>"%id.encode()))

    obj = SMArtOntology()[obj_type]
    return to_ret(request, record_id, **kwargs)

def record_delete_object(request,  record_id, obj_type, **kwargs):
    def to_ret(request,  record_id, **kwargs):
        c = RecordStoreConnector(Record.objects.get(id=record_id))
        id = smart_base + request.path                
        print "query and delete on", id
        if ('external_id' in kwargs):            
            id = obj.internal_id(c, kwargs['external_id'])
            assert (id != None), "No %s was found with external_id %s"%(obj.type, kwargs['external_id'])
        return rdf_delete(c, obj.query_one("<%s>"%id.encode()))
    
    obj = SMArtOntology()[obj_type]
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

    obj = SMArtOntology()[obj_type]
    restrict = SMArtOntology()[restrict_type]
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

    obj = SMArtOntology()[obj_type]
    restrict = SMArtOntology()[restrict_type]
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

    print "Getting objtype", kwargs
    obj = SMArtOntology()[obj_type]
    
    parent_obj = SMArtOntology()[parent_obj_type]
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

    obj = SMArtOntology()[obj_type]
    parent_obj = SMArtOntology()[parent_obj_type]
    return to_ret(request, record_id, **kwargs)

f = open(os.path.join(settings.APP_HOME, "smart/document_processing/schema/smart.owl")).read()
m = RDF.Model()
p = RDF.Parser()
p.parse_string_into_model(m, f, "nodefault")

ontology = TypeInfo.find_all_types(m)
api_calls = CallInfo.find_all_calls(m)

# hook to build in demographics-specific behavior: 
# if a record doesn't exist, create it before adding
# demographic data
def put_demographics(request, record_id, obj_type, parent_obj_type=None, **kwargs):
  try:
    Record.objects.get(id=record_id)
  except:
    Record.objects.create(id=record_id)
  record_delete_object(request, record_id, obj_type, **kwargs)
  return record_post_objects(request, record_id, obj_type, parent_obj_type, **kwargs)
  
ontology["http://xmlns.com/foaf/0.1/Person"].post = put_demographics
ontology["http://xmlns.com/foaf/0.1/Person"].put = put_demographics