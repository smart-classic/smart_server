import re, uuid
from django.conf import settings
from smart.common.rdf_ontology import api_types, api_calls, ontology
from rdf_rest_operations import *
from smart.common.util import remap_node, parse_rdf, get_property, LookupType, URIRef, sp, rdf, default_ns
from graph_augmenter import augment_data
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
                return cls.known_types_dict[URIRef(key.encode())]

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
        return str(self.smart_type.node)
    
    @property
    def node(self):
        return self.smart_type.node

    @property
    def path(self):
        v = self.smart_type.base_path
        if v: return str(v)
        return None    
         
    def internal_id(self, record_connector, external_id):
        idquery = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            CONSTRUCT {%s <http://smartplatforms.org/terms#externalIDFor> ?o.}
            FROM $context
            WHERE {
                    %s <http://smartplatforms.org/terms#externalIDFor> ?o.
                  }  """%(external_id.n3(), external_id.n3())
        print "querying", idquery
        id_graph = parse_rdf(record_connector.sparql(idquery))


        l = list(id_graph)
        if len(l) > 1:
            raise Exception( "MORE THAN ONE ENTITY WITH EXTERNAL ID %s : %s"%(external_id, ", ".join([str(x[0]) for x in l])))

        try:
            s =  l[0][2]
            print "FOUND an internal id", s
            return s
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
        
        return URIRef(ret)    

    def assert_never_a_subject(self, g, s):
        t = g.triples((s, None, None))
        assert len(list(t)) == 0, "Can't make statements about an external URI: %s"%s

    def determine_remap_target(self,g,c,s,var_bindings):
        full_path = None

        if type(s) == Literal: return None
        node_type = get_property(g, s, rdf.type)                
        subject_uri = str(s)
        
        if type(s) == BNode:
            assert node_type != None, "%s is a bnode with no type"%s.n3()
            t = RecordObject[node_type]
            if (t.path == None): return None

        elif type(s) == URIRef:
            if subject_uri.startswith("urn:smart_external_id:"):
                full_path = self.internal_id(c, s)
                assert full_path or node_type != None, "%s is a new external URI node with no type"%s.n3()
                if full_path == None:
                    t = RecordObject[node_type]
                    assert t.path != None, "Non-gettable type %s shouldn't be a URI node."%t
            elif subject_uri.startswith(smart_path("")):
                return None
            else:
                self.assert_never_a_subject(g,s)
                return None
                    
        # If we got here, we need to remap the node "s".
        if full_path == None:
            print "didn't exist before"
            full_path = t.determine_full_path(var_bindings)
        return full_path


    def generate_uris(self, g, c, var_bindings=None):   
        node_map = {}    
        nodes = set(g.subjects()) | set(g.objects())

        for s in nodes:
            new_node = self.determine_remap_target(g,c,s, var_bindings)
            if new_node: node_map[s] = new_node

        print "remapping", node_map
        for (old_node, new_node) in node_map.iteritems():
            remap_node(g, old_node, new_node)
            if type(old_node) == URIRef:
                g.add((old_node, sp.externalIDFor, new_node))


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

      ma = c.sparql(a.query_all())
      m = parse_rdf(ma)

      mae = c.sparql(ae.query_all())
      parse_rdf(mae, model=m)

      return rdf_response(serialize_rdf(m))

