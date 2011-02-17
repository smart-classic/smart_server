import re, RDF, uuid
from django.conf import settings
from smart.common.rdf_ontology import api_types, api_calls, ontology
from rdf_rest_operations import *
from smart.common.util import remap_node, parse_rdf, LookupType
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
        try: return cls.known_types_dict[key]
        except: 
            try: return cls.known_types_dict[key.node]
            except: 
                return cls.known_types_dict[RDF.Node(uri_string=key.encode())]

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
        
    def path_var_bindings(self, request_path):
        var_names =  re.findall("{(.*?)}",self.path)
        
        match_string = self.path
        for i,v in enumerate(var_names):
            # Force all variables to match, except the final one
            # (which can be a new GUID, substituted in on-the-fly.)
            repl = i+1 < len(var_names) and "([^\/]+).*" or "([^\/]*?)"
            match_string = re.sub("{"+v+"}", repl, match_string)
        matches = re.search(match_string, request_path).groups()
        var_values = {}
  
        for i,v in enumerate(var_names):
            var_values[v] = matches[i]
  
        return var_values
    
    def determine_full_path(self, var_bindings=None):
        ret = settings.SITE_URL_PREFIX + self.path
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
            
            # Let's just remap nodes that *lack* a URI
            if (s.subject.is_resource()): continue
            
            if s.subject not in node_map:
                full_path = self.determine_full_path(var_bindings)                
                node_map[s.subject] = RDF.Node(uri_string=full_path)

        for (old_node, new_node) in node_map.iteritems():
            remap_node(g, old_node, new_node)

        for c in self.children:
            c.generate_uris(g, var_bindings)

        return node_map.values()
    
    def query_one(self, id,filter_clause=""):
        ret = self.smart_type.query(one_name=id,filter_clause=filter_clause)
        return ret

    def query_all(self, above_type=None, above_uri=None,filter_clause=""):
        atype = above_type and above_type.smart_type or None
        return self.smart_type.query(above_type=atype, above_uri=above_uri,filter_clause=filter_clause)
    
for t in api_types:
    RecordObject(t)

class RecordCallMapper(object):
    def __init__(self, call):
        self.call = call
        self.obj = RecordObject[self.call.target]

    @property
    def get(self): return None
    @property
    def delete(self): return None
    @property
    def post(self): return self.obj.post
    @property
    def put(self): return self.obj.put

    @property
    def map_score(self):
        cat = str(self.call.category)
        if cat.startswith("record") and cat.endswith(self.ending):
            return 1
        return 0

    @property
    def arguments(self):
      r = {'obj': self.obj}      
      if self.call.above:
          r['above_obj'] = RecordObject[self.call.above]
      return r

    @property
    def maps_to(self):
        m = str(self.call.method)

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
    def get(self): return self.obj.get_all
    @property
    def delete(self): return self.obj.delete_all
    ending = "_items"

@CallMapper.register
class RecordItemCallMapper(RecordCallMapper):
    @property
    def get(self): return self.obj.get_one
    @property
    def delete(self): return self.obj.delete_one
    ending = "_item"


@CallMapper.register(category="record_items",
                     method="GET",
                     target="http://smartplatforms.org/terms#LabResult",
                     filter_func=lambda c: str(c.path).find("loinc")>-1)
def record_get_filtered_labs(request, *args, **kwargs):
      record_id = kwargs['record_id']
      loincs = kwargs['comma_separated_loincs'].split(",")

      filters = " || ".join (["?filteredLoinc = <http://loinc.org/codes/%s>"%s 
                              for s in loincs])

      l = RecordObject["http://smartplatforms.org/terms#LabResult"]
      c = RecordStoreConnector(Record.objects.get(id=record_id))
      q =  l.query_all(filter_clause="""
        {
          ?root_subject <http://smartplatforms.org/terms#labName> ?filteredLab.
          ?filteredLab <http://smartplatforms.org/terms#code> ?filteredLoinc.
        }  FILTER (%s)"""%filters
           )
      return rdf_response(c.sparql(q))



@CallMapper.register(category="record_items",
                     method="GET",
                     target="http://smartplatforms.org/terms#Allergy")
def record_get_allergies(request, *args, **kwargs):
      record_id = kwargs['record_id']
      a = RecordObject["http://smartplatforms.org/terms#Allergy"]
      ae = RecordObject["http://smartplatforms.org/terms#AllergyException"]
      c = RecordStoreConnector(Record.objects.get(id=record_id))

      m = RDF.Model()
      p = RDF.Parser()

      ma = c.sparql(a.query_all())
      mae = c.sparql(ae.query_all())

      p.parse_string_into_model(m, ma, "none")
      p.parse_string_into_model(m, mae, "none")

      return rdf_response(serialize_rdf(m))

