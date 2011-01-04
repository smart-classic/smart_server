import re, RDF, uuid
from smart.lib.utils import  parse_rdf, LookupType
from django.conf import settings
from smart.models.rdf_ontology import api_types, api_calls, ontology
from rdf_rest_operations import *
from query_builder import QueryBuilder

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
        try: return cls.known_types_dict[key]
        except: return cls.known_types_dict[RDF.Node(uri_string=key.encode())]

    @classmethod
    def register_type(cls, smart_type, robj):
        cls.known_types_dict[smart_type.node] = robj
        
    @property
    def children(self):
        return [RecordObject[x.node]  for x in self.smart_type.contained_types.values()]
        
    @property
    def properties(self):
        return [x.property for x in self.smart_type.properties]

    @property
    def children_by_predicate(self):
        ret = {}
        for c, t in self.smart_type.contained_types.iteritems():
            ret[c] = RecordObject[t.node]
        return ret.iteritems()
    
    @property
    def uri(self):
        return str(self.smart_type.node.uri)
    
    @property
    def node(self):
        return self.smart_type.node

    @property
    def path(self):
        v = self.smart_type.base_path
        if v: return str(v)
        return None    
     
    def predicate_for_child(self, child):
        print "finding predicate for ", str(self.node), str(child.node)
        for p,c in self.children_by_predicate:
            if c == child:
                return p
        return None
    
    def internal_id(self, record_connector, external_id):
        id_graph = parse_rdf(record_connector.sparql("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            CONSTRUCT {?s <http://smartplatforms.org/external_id> "%s".}
            FROM $context
            WHERE {?s <http://smartplatforms.org/external_id> "%s".
                   ?s rdf:type %s.
                  }
        """%(external_id, external_id, "<"+(self.uri)+">")))
        
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
        assert len(still_unbound) <= 1, "Can't match path closely enough: %s given %s -- got to %s"%(self.path, var_bindings, ret)
        if len(still_unbound) ==1:
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
            t = RecordObject[s.object]
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
                                      object=self.smart_type.node)
    
        node_map = {}    
        for s in g.find_statements(q_typed_nodes):
            if s.subject not in node_map:
                full_path = self.determine_full_path(var_bindings)                
                node_map[s.subject] = RDF.Node(uri_string=full_path)

        for (old_node, new_node) in node_map.iteritems():
            self.remap_node(g, old_node, new_node)

        for c in self.children:
            c.generate_uris(g, var_bindings)

        return node_map.values()
    
    def query_one(self, id):
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

for t in api_types:
    RecordObject(t)