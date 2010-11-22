from rdf_rest_operations import *
from rdf_ontology import *


class OntologyURLMapper():
  def __init__(self):
      pass
  
  def calls_by_path(self):
      ret = {}
      for c in api_calls:
          if c.path not in ret:
              ret[c.path] = []
          if c not in ret[c.path]:
              ret[c.path].append(c)
              
      return ret.iteritems()
    
  def django_param_regex(self, v):
    return "(?P<%s>[^/]+)"%v

  def getMethods(self, calls):
    assert len(calls) > 0, "can't map path to methods if no calls are provided!"
    methodHash = {"OPTIONS": "allow_options"}

    for c in calls:
        GetCallMapper(c).map_call(methodHash)
    
    return methodHash      

  def getArguments(self, calls):
      r = {}
      r['ontology'] = ontology      
      GetCallMapper(calls[0]).arguments(r)
      return r
      
  # get from an absolute OWL path to a relative django-friendly URL match
  def django_path(self, calls):
    ret = calls[0].path
    ret  = ret.split("?")[0]
    to_replace = re.findall("{(.*?)}", ret)
    for r in to_replace:
      ret = ret.replace("{%s}"%r, self.django_param_regex(r))
    
    ret = ret.replace("http://smartplatforms.org/", "^")
    return ret+"$"

def GetCallMapper(c):
    ret = None
    if c.category.endswith("items"):
        ret= MultipleItemCallMapper(c)
    elif c.category.endswith("item"):
        ret= SingleItemCallMapper(c) 
    else:
        ret= CallMapper(c)
    return ret

class CallMapper(object):
    def __init__(self, c):
        assert c != None, "Expected non-null call to map!"
        self.call = c
        
    def arguments(self, r):
      r['obj_type'] = self.call.target
      
      t = ontology[self.call.target]
      if t.parent:
          r['parent_obj_type'] = t.parent.type

      return r
      
      
    def map_call(self, hash):        
        if "GET" == self.call.method:
          hash["GET"] = self.get
    
        if "PUT" == self.call.method:
          hash["PUT"] = self.put
          # A cheap hack to support wget-driven "PUT" of 
          # resources during the initialization of the reference container.
          # (wget won't PUT -- it only POSTs... 
          # and curl barfs on PUT urls ending with /) 
          hash["POST"] = self.put
          
        if "POST" == self.call.method:
          hash["POST"] = self.post
    
        if  "DELETE" == self.call.method:
          hash["DELETE"] =self.delete    

    @property
    def obj(self): return ontology[self.call.target]

    
class SingleItemCallMapper(CallMapper):
    @property
    def get(self): return self.obj.get_one
    @property
    def post(self): return self.obj.post
    @property
    def put(self): return self.obj.put
    @property
    def delete(self): return self.obj.delete_one
    
class MultipleItemCallMapper(CallMapper):
    @property
    def get(self): return self.obj.get_all
    @property
    def post(self): return self.obj.post
    @property
    def put(self): return self.obj.put
    @property
    def delete(self): return self.obj.delete_all
