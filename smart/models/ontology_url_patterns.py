import re
from smart.common.rdf_ontology import api_types, api_calls, ontology
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
      for c in api_calls:
          ret.setdefault(c.path, set()).add(c)              
      return ret.iteritems()
    
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
    print "\n\n",ret
    return ret

class CallMapper(object):
    __mapper_registry = set()

    @classmethod 
    def map_call(cls, call):
      potential_maps = {}
      for m_class in cls.__mapper_registry:
        print "instantiating", m_class, call
        m = m_class(call) # instantiate the mapper
        precedence = m.map_score
        print "seeing precidentce", precedence, call, m
        if precedence > 0:
          potential_maps[m] = precedence
        
      in_order = sorted(potential_maps.keys(), 
                        key=lambda x: potential_maps[x])


      print call, "maps in order", in_order[-1]

      return in_order[-1]

    @classmethod
    def register(cls, *new_registrant, **options):
      if new_registrant:
        cls.__mapper_registry.add(new_registrant[0])
        return new_registrant

      method = options.pop('method', None)
      category = options.pop('category', None)
      target = options.pop('target', None)

      def ret(single_func):
        class SingleMethodMatcher(BasicCallMapper):
          @property
          def map_score(self):
            print "mapping for", method, category, target
            print "against",  str(self.call.method), str(self.call.category),str(self.call.target.uri)
            if ((not method or str(self.call.method) == method) and
                (not category or str(self.call.category) == category) and
                (not target or str(self.call.target.uri) == target)):
              return 100
            return 0
          maps_to = staticmethod(single_func)  
        cls.__mapper_registry.add(SingleMethodMatcher)
        return single_func
      return ret

class BasicCallMapper(object):
    arguments = {}
    def __init__(self, call):
      self.call = call

