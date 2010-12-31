import os, itertools, RDF
from django.conf import settings
from smart.lib.utils import default_ns

ns = default_ns()
rdf = ns['rdf']
rdfs = ns['rdfs']
owl = ns['owl']
api  = ns['api']
anyuri = RDF.Node(uri_string="http://www.w3.org/2001/XMLSchema#anyURI")

class OwlAttr(object):
    def __init__(self, name, predicate, object=anyuri, max_cardinality=1, min_cardinality=0):
        self.name = name
        self.predicate = predicate
        self.object = object
        self.min_cardinality=min_cardinality
        self.max_cardinality=max_cardinality

class OwlObject(object):
    def __init__(self, model, node):
        self.model = model
        self.node = node
        if (not hasattr(self, 'attributes')):
            self.attributes = []

class SMArtOwlObject(OwlObject):
    def __init__(self, model, node):
        super(SMArtOwlObject, self).__init__(model, node)
        for a in self.attributes:
            try: 
                v =  [x.object for x in model.find_statements(RDF.Statement(node, a.predicate, None))]
                if a.max_cardinality==1: 
                    assert len(v) < 2, "Attribute %s has max cardinality 1, but length %s"%(a.name, len(v))
                    if len(v) == 1: v = v[0]
                setattr(self, a.name, v) 
            except: setattr(self, a.name, None)
        return
            
"""Represent calls like GET /records/{rid}/medications/"""
class SMArtCall(SMArtOwlObject):
    attributes =  [OwlAttr("target", api['target']),
              OwlAttr("above", api['above']),
              OwlAttr("description", api['description']),
              OwlAttr("path", api['path']),
              OwlAttr("method", api['method']),
              OwlAttr("by_internal_id", api['by_internal_id']),
              OwlAttr("category", api['category'])]

    @classmethod
    def find_all(cls, m):
        def get_api_calls(m):
            q = RDF.Statement(None, rdf['type'], api['call'])
            r = list(m.find_statements(q))
            return r

        calls = []
        for c in get_api_calls(m):
            i = SMArtCall(m, c.subject)
            calls.append(i)
        
        cls.all = calls
        return calls


class SMArtRestriction(SMArtOwlObject):
    attributes =  [OwlAttr("property", owl['onProperty']),
                   OwlAttr("on_class", owl['onClass']),
                   OwlAttr("min_cardinality", owl['minCardinality']),
                   OwlAttr("all_values_from", owl['allValuesFrom'])]
  
"""Represent types like sp:Medication"""
class SMArtType(SMArtOwlObject):
    attributes =  [OwlAttr("example", api['example']),
                   OwlAttr("name", api['name']),
                   OwlAttr("name_plural", api['name_plural']),
                   OwlAttr("description", api['description']),
                   OwlAttr("base_path", api['base_path'])]        


    def __init__(self, model, node, calls):
        super(SMArtType, self).__init__(model, node)

        supers = [x.object for x in model.find_statements(RDF.Statement(node, rdfs['subClassOf'], None))]
    
        self.restrictions = []
        for s in supers:
            self.restrictions.append(SMArtRestriction(model, s))
            
        self.calls = filter(lambda c:  c.target == self.node, calls)
        self.children = {}
        self.properties = []
        
        for r in self.restrictions:
            if r.on_class:
                self.children[r.property] = r.on_class
            else:
                self.properties.append(r)
    
                        
    @classmethod
    def find_all(cls, m, calls):
        def get_types(m):
            q = RDF.Statement(None, rdf['type'], owl['Class'])
            r = list(m.find_statements(q))
            return r
      
        types = []
        for t in get_types(m):
            i = SMArtType(m, t.subject, calls)
            types.append(i)
        return types

class SMArtOntology(object):
    @classmethod
    def load(cls): 
        cls.store = {}
        for t in api_types:
            cls.store[t.node] = t

    def __init__(self):
        if not hasattr(SMArtOntology, "store"): SMArtOntology.load()
                
    def __getitem__(self, aname):
        try:
            return self.store[aname]
        except:
            return self.store[RDF.Node(uri_string=aname.encode())]

def parse_ontology(f):
    print "PARSING ONTOLOGY"
    m = RDF.Model()
    p = RDF.Parser()
    p.parse_string_into_model(m, f, "nodefault")
    
    global api_calls 
    global api_types
    global ontology
    
    api_calls = SMArtCall.find_all(m)  
    api_types = SMArtType.find_all(m, api_calls)
    ontology = SMArtOntology()

api_calls = None  
api_types = None 
ontology = None 

f = open(os.path.join(settings.APP_HOME, "smart/document_processing/schema/smart.owl")).read()
parse_ontology(f)
