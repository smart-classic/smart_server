import re
from record_object import api_calls, ontology, RecordObject

class OntologyURLMapper():
  def __init__(self):
      pass
  
  def calls_by_path(self):
      ret = {}
      for c in api_calls:
          ret.setdefault(c.path, set()).add(c)              
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
      GetCallMapper(list(calls)[0]).arguments(r)
      return r
      
  # get from an absolute OWL path to a relative django-friendly URL match
  def django_path(self, calls):
    ret = str(list(calls)[0].path)
    ret  = ret.split("?")[0]
    to_replace = re.findall("{(.*?)}", ret)
    for r in to_replace:
      ret = ret.replace("{%s}"%r, self.django_param_regex(r))
    
    ret = ret.replace("http://smartplatforms.org/", "^")
    return ret+"$"

def GetCallMapper(c):
    ret = None
    cat = str(c.category)
    if cat.endswith("items"):
        ret= MultipleItemCallMapper(c)
    elif cat.endswith("item"):
        ret= SingleItemCallMapper(c) 
    else:
        ret= CallMapper(c)
    return ret

class CallMapper(object):
    def __init__(self, c):
        assert c != None, "Expected non-null call to map!"
        self.call = c
        
    def arguments(self, r):
      r['obj'] = RecordObject[self.call.target]
      if self.call.above:
          r['above_obj'] = RecordObject[self.call.above]
      return r
      
      
    def map_call(self, hash):        
        if "GET" == str(self.call.method):
          hash["GET"] = self.get
    
        if "PUT" == str(self.call.method):
          hash["PUT"] = self.put
          # A cheap hack to support wget-driven "PUT" of 
          # resources during the initialization of the reference container.
          # (wget won't PUT -- it only POSTs... 
          # and curl barfs on PUT urls ending with /) 
          hash["POST"] = self.put
          
        if "POST" == str(self.call.method):
          hash["POST"] = self.post
    
        if  "DELETE" == str(self.call.method):
          hash["DELETE"] =self.delete    

    @property
    def obj(self): return RecordObject[self.call.target]

    
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