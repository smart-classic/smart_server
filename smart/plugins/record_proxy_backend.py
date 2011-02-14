import re, RDF, uuid
from django.conf import settings
from smart.common.util import remap_node, parse_rdf, LookupType
from smart.common.rdf_ontology import api_types, api_calls, ontology
from smart.lib.utils import url_request
from smart.models.rdf_rest_operations import *
from smart.models.ontology_url_patterns import CallMapper, BasicCallMapper

PROXY_BASE  = "http://sandbox-api.smartplatforms.org"

def proxy_get(request, *args, **kwargs):
    print "proxying request", request.path, args, kwargs
    url = PROXY_BASE + request.path    
    ret = url_request(url, "GET", {})
    return rdf_response(ret)

@CallMapper.register
class RecordItemProxy(BasicCallMapper):
    maps_to = staticmethod(proxy_get)
    
    @property
    def maps_p(self):
        cat = str(self.call.category)
        return cat.startswith("record_item") and str(self.call.method)=="GET"
