import re, RDF, uuid
from django.conf import settings
from smart.common.rdf_ontology import api_types, api_calls, ontology
from rdf_rest_operations import *
from smart.lib.utils import url_request
from smart.common.util import remap_node, parse_rdf, LookupType
from ontology_url_patterns import CallMapper, BasicCallMapper

assert hasattr(settings, "PROXY_CONTAINER"), "Don't import record_proxy_backend without defining a proxy server in settings.py."

def proxy_get(request, *args, **kwargs):
    print "proxying request", request.path, args, kwargs
    url = settings.PROXY_CONTAINER['BASE_URL'] + request.path    
    ret = url_request(url, "GET", {})
    return rdf_response(ret)

@CallMapper.register
class RecordItemProxy(BasicCallMapper):
    @property
    def map_score(self):
        cat = str(self.call.category)
        if cat.startswith("record_item") and str(self.call.method)=="GET":
            return 2
        return 0
    maps_to = staticmethod(proxy_get)
