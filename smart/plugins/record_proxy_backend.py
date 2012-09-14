from django.conf import settings
from smart.common.rdf_tools.util import remap_node, parse_rdf, LookupType
from smart.common.rdf_tools.rdf_ontology import api_types, api_calls, ontology
from smart.lib.utils import url_request, URLFetchException
from smart.models.rdf_rest_operations import *
from smart.models.ontology_url_patterns import CallMapper, BasicCallMapper
import smtplib
from email.mime.text import MIMEText

def proxy_get(request, *args, **kwargs):
    logmsg = " ".join("proxying request", request.path, args, kwargs)
    print logmsg
    url = settings.PROXY_BASE + request.path    
    try:
        ret = url_request(url, "GET", {})
        return rdf_response(ret)
    except URLFetchException as e:
    
        if (settings.PROXY_ERROR_NOTIFICATION):
            me = settings.PROXY_NOTIFICATION_FROM
            you = settings.PROXY_NOTIFICATION_TO

            msg = MIMEText(logmsg + "\n" + e.body)
            msg['Subject'] = settings.PROXY_NOTIFICATION_SUBJECT
            msg['From'] = me
            msg['To'] = you

            s = smtplib.SMTP(settings.PROXY_NOTIFICATION_SMTP_SERVER)
            s.sendmail(me, [you], msg.as_string())
            s.close()
            
            return HttpResponse(content=settings.PROXY_ERROR_MESSAGE_OVERRIDE, status=e.status)
        else:
            return HttpResponse(content=e.body, status=e.status)
			

@CallMapper.register
class RecordItemProxy(BasicCallMapper):
    @property
    def map_score(self):
        cat = str(self.call.category)
        if cat == "record" and str(self.call.http_method)=="GET":
            return 1000
        return 0
    maps_to = staticmethod(proxy_get)
