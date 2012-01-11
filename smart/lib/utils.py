"""
Utilities for Indivo

Ben Adida
ben.adida@childrens.harvard.edu
"""

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context, loader
from django.conf import settings
from django import http
from django.utils import simplejson
from xml.dom import minidom
import libxml2, libxslt
from oauth.oauth import HTTPRequest
try:
  from django.forms.fields import email_re
except:
  from django.core.validators import email_re
from smart.client.common.util import parse_rdf, serialize_rdf, bound_graph
from smart.client.common import rdf_ontology
import django.core.mail as mail
import logging
import string, random, re
import functools
import psycopg2
import psycopg2.extras
import httplib
import time
import django

smart_base = "http://smartplatforms.org"

# taken from pointy-stick.com with some modifications
class MethodDispatcher(object):
  def __init__(self, method_map):
    self.methods= method_map

  def resolve(self, request):
    view_func = self.methods.get(request.method, None)
    return view_func

  def __call__(self, request, *args, **kwargs):
    view_func = self.resolve(request)
    if view_func:
      return view_func(request, *args, **kwargs)
    return http.HttpResponseNotAllowed(self.methods.keys())

def is_valid_email(email):
  return True if email_re.match(email) else False

def random_string(length, choices=[string.letters]):
  # FIXME: seed!
  return "".join([random.choice(''.join(choices)) for i in xrange(length)])

def send_mail(subject, body, sender, recipient):
  # if send mail?
  if settings.SEND_MAIL:
    mail.send_mail(subject, body, sender, recipient)
  else:
    logging.debug("send_mail to set to false, would have sent email to %s" % recipient)

def render_template_raw(template_name, vars, type='xml'):
  t_obj = loader.get_template('%s.%s' % (template_name, type))
  c_obj = Context(vars)
  return t_obj.render(c_obj)

def render_template(template_name, vars, type='xml'):
  content = render_template_raw(template_name, vars, type)

  mimetype = 'text/plain'
  if type == 'xml':
    mimetype = "application/xml"
  elif type == "json":
    mimetype = 'text/json'
  return HttpResponse(content, mimetype=mimetype)


def get_element_value(dom, el):
  try:
    return dom.getElementsByTagName(el)[0].firstChild.nodeValue
  except:
    return ""

def url_interpolate(url_template, vars):
  """Interpolate a URL template
  
  TODO: security review this
  """

  result_url = url_template

  # go through the vars and replace
  for var_name in vars.keys():
    result_url = result_url.replace("{%s}" % var_name, vars[var_name])

  return result_url

def is_browser(request):
  """Determine if the request accepts text/html, in which case
     it's a user at a browser.
  """
  accept_header = request.META.get('HTTP_ACCEPT', False) or request.META.get('ACCEPT', False)
  if accept_header and isinstance(accept_header, str):
    return "text/html" in accept_header.split(',')
  return False

def get_content_type(request):
  content_type = None
  if request.META.has_key('CONTENT_TYPE'):
    content_type = request.META['CONTENT_TYPE']
  if not content_type and request.META.has_key('HTTP_CONTENT_TYPE'):
    content_type = request.META['HTTP_CONTENT_TYPE']
  return content_type
  
def get_capabilities ():
    capabilities = {}

    for t in rdf_ontology.api_calls:

        target = str(t.target)
        method = str(t.method)

        if target not in capabilities.keys():
            capabilities[target] = {"methods": []}
            
        if method not in capabilities[target]["methods"]:
            capabilities[target]["methods"].append(method)
            
    return capabilities

# some decorators to make life easier
def django_json(func):
  def func_with_json_conversion(*args, **kwargs):
    return_value = func(*args, **kwargs)
    return x_domain(HttpResponse(simplejson.dumps(return_value), mimetype='text/plain'))
  functools.update_wrapper(func_with_json_conversion, func)
  return func_with_json_conversion

def apply_xslt(sourceDOM, stylesheetDOM):
    style = libxslt.parseStylesheetDoc(stylesheetDOM)
    return style.applyStylesheet(sourceDOM, None).serialize()

def smart_path(path):
    ret = settings.SITE_URL_PREFIX + path
    return ret.encode()

def smart_parent(path):
    ret = path.split("/")
    return "/".join(ret[:-2])

def x_domain(r):
  ui = settings.SMART_UI_SERVER_LOCATION
  r['Access-Control-Allow-Origin'] = ui#"*"# "%s://%s:%s"%(ui['scheme'], ui['host'], ui['port'])
  return r


def trim(p, n):
    return '/'.join(p.split('/')[:-n]).encode()

def url_request(url,  method, headers, data=None):
    req = url_request_build(url,  method, headers, data)
    return url_request_execute(req)

def url_request_build(url,  method, headers, data=None):
  return HTTPRequest(method, url, HTTPRequest.FORM_URLENCODED_TYPE, data, headers)

def url_request_execute(req):
    (scheme, url) = req.path.split("://")
    domain = url.split("/")[0]
    path = "/"+"/".join(url.split("/")[1:])
    conn = None
    
    if (scheme == "http") :        
        conn = httplib.HTTPConnection(domain)
    elif (scheme == "https"):
        conn = httplib.HTTPSConnection(domain)

    data = req.data
    if (req.method == "GET"):
        path += "?%s"%data
        data = None

    #print "URL_REQUEST:", domain, req.method, path, data, req.headers        
    conn.request(req.method, path, data, req.headers)
    r = conn.getresponse()

    if (r.status == 200):
        data = r.read()
        conn.close()
        return data
    elif (r.status == 204):
        conn.close()
        return True
    
    
    else: raise Exception("Unexpected HTTP status %s"%r.status)

def rdf_response(s):
    return x_domain(HttpResponse(s, mimetype="application/rdf+xml"))

def rdf_get(record_connector, query):
    res = record_connector.sparql(query)    
    return rdf_response(res)

def rdf_delete(record_connector, query, save=True): 
    to_delete = parse_rdf(record_connector.sparql(query))
    deleted = bound_graph()

    for r in to_delete:
       deleted.add(r)
       record_connector.pending_removes.append(r)
       
    if (save): record_connector.execute_transaction()
       
    return rdf_response(serialize_rdf(deleted))

def rdf_post(record_connector, new_g):
    for s in new_g:
        record_connector.pending_adds.append(s)

    record_connector.execute_transaction()
    return rdf_response(serialize_rdf(new_g))

alnum_pattern = re.compile('^a-zA-Z0-9_+')

def string_to_alphanumeric(s):
  return alnum_pattern.sub('', s)

logging.basicConfig(
      level = logging.DEBUG,
      format = '%(asctime)s %(levelname)s %(message)s',
      )

class DjangoVersionDependentExecutor(object):
    """ class which will execute different code based on Django's version.

    Syntax for a version requirement is ``{major}.{minor}.{revision}[+|-]``, 
    where the optional ``+`` and ``-`` indicate whether to include versions 
    after or before the given release, respectively.

    """

    def __init__(self, version_map, default_return_val=None):
        """ create the object.

        version_map is a dictionary of ``version_requirement:callable`` pairs.
        When called, the object will execute all callables in the 
        dictionary that corresponds to a version_requirement satisfied by the
        current Django version.

        If no such callables exist, calling the object will return
        ``default_return_val``. Otherwise, the call will return the value
        returned by the last callable to be executed. Note that, since there
        is no specified ordering on the callables, this could be the result
        of any passed callable. For this reason, it is a good idea to pass
        callables that all return values of equivalent types.
        
        """
        self.django_v = django.VERSION[0:3]
        self.ret = default_return_val
        self.funcs = []

        for version_string, func in version_map.iteritems():
            if version_string[-1] in ('+', '-'):
                direction = version_string[-1]
                version_string = version_string[:-1]

            req_v = tuple(map(int, version_string.split('.'))[0:3])

            if (req_v < self.django_v and direction == '+') \
                    or (req_v > self.django_v and direction == '-') \
                    or (req_v == self.django_v):
                self.funcs.append(func)

    def __call__(self, *args, **kwargs):
        ret_val = self.ret
        for func in self.funcs:
            ret_val = func(*args, **kwargs)
        return ret_val
