from django.conf import settings
from smart.client.common.util import remap_node, parse_rdf, LookupType
from smart.client.common.rdf_ontology import api_types, api_calls, ontology
from smart.lib.utils import url_request, URLFetchException
from smart.models.rdf_rest_operations import *
from smart.models.ontology_url_patterns import CallMapper, BasicCallMapper

def proxy_get(request, *args, **kwargs):
    print "proxying request", request.path, args, kwargs
    url = settings.PROXY_BASE + request.path    
    try:
        ret = url_request(url, "GET", {})
        return rdf_response(ret)
    except URLFetchException as e:
        return HttpResponse(content=e.body, status=e.status)
			

@CallMapper.register
class RecordItemProxy(BasicCallMapper):
    @property
    def map_score(self):
        cat = str(self.call.category)
        if cat.startswith("record_item") and str(self.call.method)=="GET":
            return 1000
        return 0
    maps_to = staticmethod(proxy_get)
