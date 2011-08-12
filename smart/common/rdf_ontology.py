from query_builder import QueryBuilder
from util import *
import string, re

class OWL_Base(object):
    __metaclass__ = LookupType
    store = {}
    attributes = {}

    data_properties = None

    def guess_name(self):
        return re.split("[#\/]", str(self.uri))[-1]

    @classmethod 
    def find_all_data_properties(cls, graph):        
        OWL_Base.data_properties = {}
        for p in graph.triples((None, rdf.type, owl.DatatypeProperty)):
                OWL_Base.data_properties[p[0]] = True

    def get_annotation(self, p):
        try:
            return filter(lambda x:  x.uri==p, self.annotations)[0].value
        except: return None

    def get_property(self, p):
        return [x[2] for x in self.graph.triples((self.uri, p, None))]

    @property
    def index_key(self):
        return self.uri


    def __init__(self, graph, uri):
        self.uri = uri
        self.graph = graph
        for (pn, v) in self.attributes.iteritems():
            try:
                if type(v) is tuple:
                    setattr(self, pn, v[1](self.get_property(v[0])[0]))
                else:
                    setattr(self, pn, self.get_property(v)[0])
            except: setattr(self, pn, None)

        if self.__class__.data_properties == None:
            OWL_Base.find_all_data_properties(graph)

    @classmethod
    def get_or_create(cls, graph, node, *args, **kwargs):
        if cls.store.has_key(node): return cls.store[node]
        n = cls(graph, node, *args, **kwargs)
        cls.store[n.index_key] = n
        return n

    @classmethod
    def __getitem__(cls, key):
        try: return cls.store[key]
        except: 
            k = str(key)
            return cls.store[URIRef(k)]

class OWL_Datatype(OWL_Base):
    attributes = {
        "on_datatype": owl.onDatatype
        }

class OWL_Restriction(OWL_Base):
    attributes = {
            "on_property": owl.onProperty,
            "on_class": owl.onClass,
            "min_qcardinality": (owl.minQualifiedCardinality, lambda x: int(x)),
            "max_qcardinality": (owl.maxQualifiedCardinality, lambda x: int(x)),
            "min_cardinality": (owl.minCardinality, lambda x: int(x)),
            "max_cardinality": (owl.maxCardinality, lambda x: int(x)),
            "cardinality": (owl.cardinality, lambda x: int(x)),
            "all_values_from": owl.allValuesFrom,
            }
        
    def __init__(self, graph, uri):
        super(OWL_Restriction, self).__init__(graph, uri)

        self.is_simple_subclass = type(uri) is URIRef

        # This could be a simple subclass restriction (a subclassOf b).
        try:
            dr = self.data_properties[self.on_property]
        except:
            dr = False

        self.is_data_property = dr and self.on_property
        self.is_object_property = (not dr) and self.on_property

        # We don't yet deal with arbitrary anonymous constraint expressions
        # like "(drugName only (code only RxNorm_Semantic))"...
        # Just allow predicates to conenct with concrete URI classes.
        if (type(self.all_values_from) == BNode):
            self.all_values_from = None

class OWL_Class(OWL_Base):
    store = {}


    def __init__(self, graph, uri):
        assert uri != None, "Expect a non-null URI"
        super(OWL_Class, self).__init__(graph, uri)
        self.subclass_restrictions = self.find_subclass_restrictions()

        self.parent_classes = self.find_parent_classes()
        self.object_properties = self.find_object_properties()
        self.data_properties = self.find_data_properties()

        self.annotations = self.find_annotations()

    def find_subclass_restrictions(self):
        ret = []
        for r in self.get_property(rdfs.subClassOf):
            ret.append(OWL_Restriction(self.graph, r))
        return ret

    def find_parent_classes(self):
        parents = filter(lambda c: c.is_simple_subclass, self.subclass_restrictions)
        ret = []
        for p in parents:
            try: assert p.uri != self.uri, "class is its own parent: %s"%p.uri
            except: continue
            pclass = self.get_or_create(self.graph, p.uri)
            ret += pclass.parent_classes
            ret.append(pclass)
        return ret

    def grouped_properties(self, ret=None, filter_fn=lambda x: True):
        if ret == None: ret  = {}

        for pc in self.parent_classes:
            pc.grouped_properties(ret, filter_fn)

        for p in self.subclass_restrictions:
            if filter_fn(p):
                a = ret.setdefault(p.on_property, [])
                a.append(p)
        return ret

    def find_object_properties(self):
        ret = []
        def property_added(p):
            return p.uri in [prop.uri for prop in ret]

        ops = self.grouped_properties(filter_fn=lambda x: x.is_object_property)
        for uri, restrictions in ops.iteritems():
            ret.append(OWL_ObjectProperty(self.graph, self, uri, restrictions))
        return filter(lambda x: x.has_nonzero_cardinality, ret)

    def find_data_properties(self):
        ret = []
        def property_added(p):
            return p.uri in [prop.uri for prop in ret]

        dps = self.grouped_properties(filter_fn=lambda x: x.is_data_property)
        for uri, restrictions in dps.iteritems():
            ret.append(OWL_DataProperty(self.graph, self, uri, restrictions))
        return filter(lambda x: x.has_nonzero_cardinality, ret)

    def find_annotations(self):
        ret = []
        for a in self.graph.triples((None, rdf.type, owl.AnnotationProperty)):
            a = a[0]
            try:
                ret.append(OWL_Annotation(self.graph, self, a, self.get_property(a)[0]))
            except: pass
        return ret

class OWL_Annotation(object):
    def __init__(self, graph, from_class, uri, value):
        self.from_class = from_class
        self.uri = uri
        self.value = str(value)

class OWL_Property(OWL_Base):

    property_annotations = None

    @property
    def multiple_cardinality(self):
        return  (self.cardinality and self.cardinality > 1) or \
            (self.max_cardinality and self.max_cardinality > 1) or \
            (self.max_qcardinality and self.max_qcardinality > 1) or \
            (not (self.cardinality or self.max_cardinality or self.max_qcardinality))
    
    @property
    def cardinality_string(self):
        if self.cardinality:
            return str(self.cardinality)
        ret = ""
        if self.min_cardinality != None:
            ret += str(self.min_cardinality) + " - "
        elif self.min_qcardinality != None:
            ret += str(self.min_qcardinality) + " - "
        else: ret += "0 - "
 
        if self.max_cardinality != None:
            ret += str(self.max_cardinality)
        elif self.max_qcardinality != None:
            ret += str(self.max_qcardinality)
        else: ret += "Many"
        return ret
        


    @classmethod 
    def find_all_annotations(cls, graph):
        if OWL_Property.property_annotations != None: 
            return

        OWL_Property.property_annotations = {}

        q = """
            PREFIX owl:<http://www.w3.org/2002/07/owl#>
            PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
               SELECT ?from_class ?on_property ?annotation_property ?annotation_value
               WHERE {
                      ?axiom rdf:type owl:Axiom.
                      ?annotation_property rdf:type owl:AnnotationProperty.
                      ?axiom ?annotation_property ?annotation_value.
                      ?axiom owl:annotatedSource ?from_class.
                      ?axiom owl:annotatedProperty rdfs:subClassOf.
                      ?axiom owl:annotatedTarget ?target.
                      ?target owl:onProperty ?on_property.
               }"""
        
        for annotation  in graph.query(q):
            akey = annotation[0].n3() + "."+annotation[1].n3()
            akey_vals = OWL_Property.property_annotations.setdefault(akey, [])
            akey_vals.append(annotation)

    def merge_values_from(self, other, include_nulls=False):
        for (an, v) in other.attributes.iteritems():
            if include_nulls or getattr(other, an) != None:
                setattr(self, an, getattr(other,an))


    # TODO:  query only once for all annotations to speed things up.
    def find_annotations(self):

        if OWL_Property.property_annotations == None:
            OWL_Property.find_all_annotations(self.graph)

        ret = []
        try:
            akey = self.from_class.uri.n3()+"."+ self.uri.n3()
            about_me = self.__class__.property_annotations[akey]
            for a in about_me:
                ret.append(OWL_Annotation(self.graph, self, a[2], a[3]))
        except KeyError: 
            pass
        return ret

    @property
    def has_nonzero_cardinality(self):
        return (self.max_cardinality or self.cardinality or self.max_qcardinality) != 0

    def __init__(self, graph, from_class, uri, restrictions):
        self.debug = restrictions
        self.graph = graph
        self.from_class = from_class
        self.uri = uri

        is_first = True
        for r in restrictions:
            self.merge_values_from(r, is_first)
            is_first = False

        if self.on_class and self.all_values_from:
            assert self.on_class == self.all_values_from, \
                "%s OnClass must equal AllValuesFrom: %s vs. %s"%(self.uri, self.on_class, self.all_values_from)

        self.annotations = self.find_annotations()
        self.description = self.get_annotation(rdfs.comment) or ""
        self.name = self.get_annotation(rdfs.label) or self.guess_name()


class OWL_ObjectProperty(OWL_Property):
    @property
    def to_class(self):
        to_class_uri = self.on_class or self.all_values_from
        return self.from_class.get_or_create(self.graph, to_class_uri)

    def __init__(self, graph, from_class, uri, restrictions):
        super(OWL_ObjectProperty, self).__init__(graph, from_class, uri, restrictions)

class OWL_DataProperty(OWL_Property):
    def __init__(self, graph, from_class, uri, restrictions):
        super(OWL_DataProperty, self).__init__(graph, from_class, uri, restrictions)

class SMART_Class(OWL_Class):
    __metaclass__ = LookupType

    @property
    def is_statement(self):
        parent_class_uris = [c.uri for c in self.parent_classes]
        return URIRef("http://smartplatforms.org/terms#Statement") in parent_class_uris

    def __init__(self, graph, uri):
        super(SMART_Class, self).__init__(graph, uri)
        self.name = self.get_annotation(rdfs.label) or self.guess_name()
        self.description = self.get_annotation(rdfs.comment)
        self.example = self.get_annotation(api.example)
        self.base_path = self.get_annotation(api.base_path)

        self.calls = []
        for call in graph.triples((None, api.target, uri)):
            self.calls.append(SMART_API_Call.get_or_create(graph, call[0]))

"""Represent calls like GET /records/{rid}/medications/"""
class SMART_API_Call(OWL_Base):
    rdf_type = api.call
    store = {}
    attributes =  {
        "target": api.target,
        "description": rdfs.comment,
        "path": api.path,
        "method": api.method,
        "by_internal_id": api.by_internal_id,
        "category": api.category
        }


parsed = False
                
def parse_ontology(f):
    m = parse_rdf(f)

    global api_calls 
    global api_types
    global parsed
    
    m = parse_rdf(f)
    for c in m.triples((None, rdf.type, owl.Class)):
        o = SMART_Class.get_or_create(m, URIRef(c[0]))

    api_calls = SMART_API_Call.store.values()
    api_types = SMART_Class.store.values()
    parsed = True

api_calls = None  
api_types = None 
ontology = SMART_Class

f = None
try:
  from django.conf import settings
  f = open(settings.ONTOLOGY_FILE).read()
except: pass

if f != None:
  parse_ontology(f)
