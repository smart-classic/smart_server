import re
from smart.client.common.rdf_ontology import api_types, api_calls, ontology
from django.conf.urls.defaults import patterns
from smart.lib.utils import MethodDispatcher

class OntologyURLMapper():
  def __init__(self, urlpatterns):
      self.patterns = urlpatterns

      for p, calls in self.calls_by_path():
        methods = {}
        arguments = {}

        for c in calls:
          mapper = CallMapper.map_call(c)
          methods[str(c.method)] = mapper.maps_to
          arguments.update(mapper.arguments)
        self.patterns += patterns( '',
                                 (self.django_path(p),
                                  MethodDispatcher(methods), 
                                  arguments))
  
  def calls_by_path(self):
      ret = {}

      print "got calls", len(api_calls)
      for c in api_calls:
        print "setting path", c.path, c
        ret.setdefault(c.path, set()).add(c)

      calls = ret.keys()
      calls = sorted(calls, key=lambda x: -1*len(str(x)))
      ret = zip(calls, [ret[c] for c in calls])
      return ret
    
  def django_param_regex(self, v):
    return "(?P<%s>[^/]+)"%v

      
  # get from an absolute OWL path to a relative django-friendly URL match
  def django_path(self, path):
    ret = str(path)
    ret  = ret.split("?")[0]
    to_replace = re.findall("{(.*?)}", ret)
    for r in to_replace:
      ret = ret.replace("{%s}"%r, self.django_param_regex(r))
    assert ret[0]=="/", "Expect smart.owl to provide absolute paths"
    
    ret = "^" + ret[1:] + "$"
    return ret

class CallMapper(object):
    __mapper_registry = set()

    @classmethod 
    def map_call(cls, call):
      potential_maps = {}
      for m_class in cls.__mapper_registry:
        m = m_class(call) # instantiate the mapper
        precedence = m.map_score
        if precedence > 0:
          potential_maps[m] = precedence

      in_order = sorted(potential_maps.keys(), 
                        key=lambda x: potential_maps[x])
      return in_order[-1]

    @classmethod
    def register(cls, *new_registrant, **options):
      if new_registrant:
        cls.__mapper_registry.add(new_registrant[0])
        return new_registrant

      method = options.pop('method', None)
      category = options.pop('category', None)
      target = options.pop('target', None)
      filter_func = options.pop('filter_func', None)
      path = options.pop('path', None)

      def ret(single_func):
        class SingleMethodMatcher(BasicCallMapper):
          @property
          def maps_p(self):
            return  ((not method or str(self.call.method) == method) and
                     (not category or str(self.call.category) == category) and
                     (not target or str(self.call.target) == target) and 
                     (not path or str(self.call.path) == path) and 
                     (not filter_func or filter_func(self.call)))
          maps_to = staticmethod(single_func)  
        cls.__mapper_registry.add(SingleMethodMatcher)
        return single_func
      return ret

class BasicCallMapper(object):
    arguments = {}
    def __init__(self, call):
      self.call = call

    @property
    def map_score(self):
      if self.maps_p: return 100
      return 0
