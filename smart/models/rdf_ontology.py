from rdf_objects import *

class CallInfo(object):
  def __init__(self, m, c):
    self.model = m

    try: self.target = [str(x.object.uri) for x in m.find_statements(RDF.Statement(c, sp['api/target'], None))][0]
    except: self.target = None

    try: self.above = [str(x.object.uri) for x in m.find_statements(RDF.Statement(c, sp['api/above'], None))][0]
    except: self.above = None

    try: self.description = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(c, sp['api/description'], None))][0]
    except: self.description = None

    try: self.path = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(c, sp['api/path'], None))][0]
    except: self.path = None

    try: self.method = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(c, sp['api/method'], None))][0]
    except: self.method = None

    try: self.by_internal_id = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(c, sp['api/by_internal_id'], None))][0]
    except: self.by_internal_id = None

    try: self.category = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(c, sp['api/category'], None))][0]
    except: self.category = None

    return

  @property
  def sort_order(self):
      m = {"GET" : 10, "POST":20,"PUT":30,"DELETE":40}    
      ret =  m[self.method]
      if ("items" in self.category): ret -= 1
      return ret
  
  @classmethod
  def find_all_calls(cls, m):
    def get_api_calls(m):
      q = RDF.Statement(None, rdf['type'], sp['api/call'])
      r = list(m.find_statements(q))
      return r

    calls = []
    for c in get_api_calls(m):
      i = CallInfo(m, c.subject)
      calls.append(i)
    return calls

  def sorted_methods(self):
      ret = []
      if "GET" in self.methods: ret.append("GET")
      for m in self.methods:
          if m not in ret: ret.append(m)
      return ret

class TypeInfo(object):
  def __init__(self, m, t, calls):
    self.model = m

    supers = [x.object for x in m.find_statements(RDF.Statement(t, rdfs['subClassOf'], None))]

    properties = []
    children = {}
    for s in supers:
      prop = [str(x.object.uri) for x in m.find_statements(RDF.Statement(s, owl['onProperty'], None))][0]
      kids = [str(x.object.uri) for x in m.find_statements(RDF.Statement(s, owl['onClass'], None))]

      # Is this a property (no kids) or a child (with kids)?
      if len(kids) == 0: properties.append(prop)
      else: children[prop] = kids[0]

    self.properties = properties
    self.children = children
        
    self.type = str(t.uri)

    try:
        self.example = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(t, sp['api/example'], None))][0]
    except: self.example = None
    
    try:
        self.name = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(t, sp['api/name'], None))][0]
    except: self.name = None
    try:
        self.name_plural = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(t, sp['api/name_plural'], None))][0]
    except: self.name_plural = None
    try:
        self.description = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(t, sp['api/description'], None))][0]
    except: self.description = None
    
    try:
        self.path = [str(x.object.literal_value['string']) for x in m.find_statements(RDF.Statement(t, sp['api/base_path'], None))][0]
    except:
        self.path = None

    
    self.calls = []
    for c in calls:
        if  self.type == c.target:
            self.calls.append(c)
    
    return

  @property
  def sort_order(self):
      return self.calls[0].category.split("_")[0].capitalize()

  def populate_rdfobject(self, by_type):
    u = self.type
    if u not in by_type: by_type[u] = RDFObject()          

    by_type[u].type = self.type
    if (self.path != None):
        by_type[u].path = self.path
     # add properties  
    for p in self.properties:
      by_type[u].properties.append(RDFProperty(p))    
    
    # add children
    for (cname, cval) in self.children.iteritems():
      if cval not in by_type:
        by_type[cval] = RDFObject()
      by_type[cval].parent = by_type[u]
      by_type[u].children[cname] = by_type[cval]

  def property_description(self, p):
      q = RDF.SPARQLQuery("""
        BASE <http://smartplatforms.org/>
        PREFIX sp:<http://smartplatforms.org/>
        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl:<http://www.w3.org/2002/07/owl#>
        PREFIX api:<http://smartplatforms.org/api/>
        PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?name ?desc
        WHERE {
        <%s>  rdfs:subClassOf ?super.
        ?super owl:onProperty <%s>.
        ?super api:doc ?d.
        ?d api:name ?name.
        ?d api:description ?desc.
        }
        """ % (self.type, p))

      vals = list(q.execute(self.model))
      
      assert len(vals) <= 1, "expect at most one api:doc element for a given property"
      return vals[0]['name'].literal_value['string'], vals[0]['desc'].literal_value['string']

  @classmethod
  def find_all_types(cls, m):
    def get_types(m):
      q = RDF.Statement(None, rdf['type'], owl['Class'])
      r = filter(lambda x: str(x.subject.uri), list(m.find_statements(q)))
      return [v.subject for v in r]

    calls = CallInfo.find_all_calls(m)
    types = {}

    for t in get_types(m):
      types[str(t.uri)] = TypeInfo(m, t, calls)

    return types

  @classmethod
  def populate_ontology(cls, api_types):
    by_type = {}
    for tn, t in api_types.iteritems():
        t.populate_rdfobject(by_type)
    SMArtOntology.set(by_type)
    return SMArtOntology()

class SMArtOntology(object):
  @classmethod
  def set(cls, by_type):
    cls.by_type = by_type

  def __getitem__(self, v):
    if v == None: return None
    return self.by_type[v]

f = open(os.path.join(settings.APP_HOME, "smart/document_processing/schema/smart.owl")).read()
m = RDF.Model()
p = RDF.Parser()
p.parse_string_into_model(m, f, "nodefault")

api_types = TypeInfo.find_all_types(m)
ontology = TypeInfo.populate_ontology(api_types)
RDFObject.ontology = ontology
api_calls = CallInfo.find_all_calls(m)

