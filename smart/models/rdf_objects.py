import re, RDF, os, uuid
from smart.models.rdf_store import RecordStoreConnector
from smart.models.records import Record
from smart.lib.utils import default_ns, trim, smart_base, smart_parent, smart_path, smart_external_path, rdf_get, rdf_post, rdf_delete, parse_rdf, serialize_rdf
from django.conf import settings
from rdf_rest_operations import *

NS = default_ns()
sp  = RDF.NS("http://smartplatforms.org/")
rdf = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
owl = RDF.NS("http://www.w3.org/2002/07/owl#")
rdfs = RDF.NS("http://www.w3.org/2000/01/rdf-schema#")


class RDFProperty(object):
    def __init__(self, predicate, object=None):
        self.predicate = predicate
        self.object = object

class RDFObject(object):
    def __init__(self, intype=None, path=None):
        self.type = intype
        self.path=path
        self.parent = None
        self.properties = [RDFProperty(predicate=str(NS['rdf']['type'].uri)), 
                           RDFProperty(predicate=str(NS['sp']['external_id'].uri))]
        self.children = {}
        self.get_one = record_get_object
        self.get_all = record_get_all_objects
        self.delete_one = record_delete_object
        self.delete_all = record_delete_all_objects
        self.post = record_post_objects
        self.put = record_put_object

    def predicate_for_child(self, child):
        print "finding predicate for ", self.type, child.type
        for (p,c) in self.children.iteritems():
            if c == child:  return p
        return None
    
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
            print "FOUND an internal id", s
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
        stripped = child_type.path.replace(self.path, "")
        stripped = re.sub("{.*?}", "", stripped)
        return stripped

    def path_var_bindings(self, request_path):
      var_names =  re.findall("{(.*?)}",self.path)
      
      match_string = self.path
      for i,v in enumerate(var_names):
          # Force all variables to match, except the final one
          # (which can be a new GUID, substituted in on-the-fly.)
          repl = i+1 < len(var_names) and "([^\/]+).*" or "([^\/]*?)"
          match_string = re.sub("{"+v+"}", repl, match_string)
      print "re.search", match_string, request_path,re.search(match_string, request_path).groups()
      matches = re.search(match_string, request_path).groups()
      var_values = {}

      for i,v in enumerate(var_names):
        var_values[v] = matches[i]

      return var_values        
    
    def determine_full_path(self, var_bindings=None):
        ret  = self.path
        for vname, vval in var_bindings.iteritems():
            if vval == "": vval="{new_id}"
            ret = ret.replace("{"+vname+"}", vval)

        still_unbound = re.findall("{(.*?)}",ret)
        assert len(still_unbound) == 1, "Can't match path closely enough: %s given %s -- got to %s"%(self.path, var_bindings, ret)
        ret = ret.replace("{"+still_unbound[0]+"}", str(uuid.uuid4()))
        
        return ret.encode()
    
    def ensure_only_one_put(self, g):
        qs = RDF.Statement(subject=None, 
                   predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                   object=None)
    
        typed_object_count = 0
        errors = []
        for s in g.find_statements(qs):
            # If this is a typed object with no externally-accessible path, it's fine
            # (stays as a blank node, doesn't trigger a PUT error)
            t = self.ontology[str(s.object.uri)]
            if (t.path == None): continue

            typed_object_count += 1
            errors.append(str(s.object))
        assert typed_object_count == 1, "You must PUT exactly one typed resource at a time; you tried putting %s: %s"%(typed_object_count, ", ".join(errors))
    
        return
    
    def generate_uris(self, g, var_bindings=None):   
	# Only give URIs to objects that support externally-referenced paths.
        if (self.path == None): return 
    
        q_typed_nodes = RDF.Statement(subject=None, 
                                      predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                                      object=self.type_node())
    
        node_map = {}    
        for s in g.find_statements(q_typed_nodes):
            if s.subject not in node_map:
                parent_path = self.find_parent(g, s.subject)
                full_path = self.determine_full_path(var_bindings)                
                node_map[s.subject] = RDF.Node(uri_string=full_path)

        for (old_node, new_node) in node_map.iteritems():
            self.remap_node(g, old_node, new_node)
        for c in self.children.values():
            c.generate_uris(g, var_bindings)

        return node_map.values()

    
    def query_one(self, id):
        print "Asked to query one for ", id
        return self.query(one_name=id)

    def query_all(self, above_type=None, above_uri=None):
        return self.query(above_type=above_type, above_uri=above_uri)

    def query(self, one_name="?root_subject", above_type=None, above_uri=None):
        ret = """
        BASE <http://smartplatforms.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        CONSTRUCT { $construct_triples }
        FROM $context
        WHERE {
           { $query_triples } 
        }
        """

        q = QueryBuilder(self, one_name)
        q.require_above(above_type, above_uri)
        b = q.build()

        ret = ret.replace("$construct_triples", q.construct_triples())
        ret = ret.replace("$query_triples", b)        
        return ret

class QueryBuilder(object):
    def __init__(self, root_type, root_name):
        self.root_type = root_type
        self.triples_created = []
        self.identifier_count = {}
        
        self.root_name = self.get_identifier(root_name)

    def construct_triples(self):
        return "\n ".join(self.triples_created)
        
    def require_above(self, above_type=None, above_uri=None):
        if (above_uri == None): return
        predicate = above_type.predicate_for_child(self.root_type)
        self.required_triple("<"+above_uri+">", "<"+predicate+">", self.root_name )
        
    def get_identifier(self, id_base, role="predicate"):
        if id_base[0] == "<": return id_base
        
        start = id_base[0] == "?" and "?" or ""

        if "/" in id_base:
          id_base = id_base.rsplit("/", 1)[1]
        if "#" in id_base:
          id_base = id_base.rsplit("#", 1)[1]

        id_base = re.sub(r'\W+', '', id_base)
        id_base = start + id_base + "_" + role

        self.identifier_count.setdefault(id_base, 0)
        self.identifier_count[id_base] += 1
        return "%s_%s"%(id_base, self.identifier_count[id_base])

    def required_triple(self, root_name, pred, obj):
        self.triples_created.append("%s %s %s. " % (root_name, pred, obj))
        return " %s %s %s. \n" % (root_name, pred, obj)

    def optional_triple(self, root_name, pred, obj):
        self.triples_created.append("%s %s %s. " % (root_name, pred, obj))
        return " OPTIONAL { %s %s %s. } \n" % (root_name, pred, obj)
        
    def optional_child(self, root_name, child, pred, obj):
        self.triples_created.append("%s %s %s. " % (root_name, pred, obj))
        ret = " OPTIONAL { %s %s %s. $insertion } \n" % (root_name, pred, obj)
        repl = self.build(obj, child)
        ret = ret.replace("$insertion", repl)
        return ret


    def build(self, root_name=None, root_type=None):
        ret = ""
        # Recursion starting off:  set initial conditions (if any).
        if root_type == None:
            root_name = self.root_name
            root_type = self.root_type            
            ret = " ".join(self.triples_created)
            
        if (root_type.type != None):
            if (root_type.path != None):
                ret += self.required_triple(root_name, "rdf:type", "<"+root_type.type+">")
            else:
                ret += self.optional_triple(root_name, "rdf:type", "<"+root_type.type+">")

        for p in root_type.properties:
            oid = self.get_identifier("?"+p.predicate, "object")
            ret  += self.optional_triple(root_name, "<"+p.predicate+">", oid)

        for (p, child) in root_type.children.iteritems():
            oid = self.get_identifier("?"+p, "object")
            ret += self.optional_child(root_name, child, "<"+p+">", oid)

        return ret
