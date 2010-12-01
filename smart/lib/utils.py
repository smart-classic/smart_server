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

from django.forms.fields import email_re
import django.core.mail as mail
import logging
import string, random
import functools

import psycopg2
import psycopg2.extras
import RDF
import httplib
import time

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

def bound_graph():
    return RDF.Model(storage=RDF.HashStorage("", options="hash-type='memory'"))

def bound_serializer(format):
    s = RDF.NTriplesSerializer()
    if (format == "xml"):
        s = RDF.RDFXMLSerializer()
        
    bind_ns(s)
    return s 


def smart_path(request):
    ret = smart_base + request.path
    return ret.encode()

def smart_external_path(request):
    ret = smart_base + request.path
    split_point = ret.rfind("external_id")
    assert (split_point >= 0), "Expected external_id in %s"%ret
    ret = ret[:split_point]
    return ret.encode()

def smart_parent(path):
    ret = path.split("/")
    return "/".join(ret[:-2])


def default_ns():
    d = {}
    d['dc'] = RDF.NS('http://purl.org/dc/elements/1.1/')
    d['dcterms'] = RDF.NS('http://purl.org/dc/terms/')
    d['med'] = RDF.NS('http://smartplatforms.org/medication#')
    d['allergy'] = RDF.NS('http://smartplatforms.org/allergy/')
    d['umls'] = RDF.NS('http://www.nlm.nih.gov/research/umls/')
    d['sp'] = RDF.NS('http://smartplatforms.org/')
    d['spdemo'] = RDF.NS('http://smartplatforms.org/demographics/')
    d['foaf']=RDF.NS('http://xmlns.com/foaf/0.1/')
    d['rdf'] = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
    d['rxn'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/')
    d['rxcui'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXCUI/')
    d['rxaui'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXAUI/')
    d['rxatn'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/RXATN#')
    d['rxrel'] = RDF.NS('http://link.informatics.stonybrook.edu/rxnorm/REL#')
    d['snomed-ct'] = RDF.NS('http://www.ihtsdo.org/snomed-ct/')
    d['ccr'] = RDF.NS('urn:astm-org:CCR')
    d['v'] = RDF.NS('http://www.w3.org/2006/vcard/ns#')
    return d

def bind_ns(serializer, ns=None):
    if (ns == None):
        ns = default_ns()
    for k in ns.keys():
        v = ns[k]
        serializer.set_namespace(k, RDF.Uri(v._prefix))

def parse_rdf(string, model=None, context="none"):
#    print "PSIM: STRING=", string
#    print "PSIM: MODEL = ", model
    if model == None:
        model = RDF.Model()
    else:
        print "We already had a model passed in." 
    parser = RDF.Parser()
#    print "Parsing into model: ", string.encode()
    parser.parse_string_into_model(model, string.encode(), context)        
    return model
        
"""Serializes a Redland model or CONSTRUCT query result with namespaces pre-set"""
def serialize_rdf(model, format="xml"):
    serializer = bound_serializer(format)

    try: return serializer.serialize_model_to_string(model)
    except AttributeError:
        try:
            tmpmodel = RDF.Model(storage=RDF.HashStorage("", options="hash-type='memory'"))
            tmpmodel.add_statements(model.as_stream())
            return serializer.serialize_model_to_string(tmpmodel)
        except AttributeError:
            return '<?xml version="1.0" encoding="UTF-8"?>'


def xslt_ccr_to_rdf(source, stylesheet="ccr_to_med_rdf"):
    sourceDOM = libxml2.parseDoc(source)
    ss = "%s%s"%(settings.XSLT_STYLESHEET_LOC, "%s.xslt"%stylesheet)
    ssDOM = libxml2.parseFile(ss)
    return apply_xslt(sourceDOM, ssDOM)

def rxn_related(rxcui_id, graph):
   rxcui_id = str(rxcui_id)
   ns = default_ns()
   literal = RDF.Node
   
   conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             (settings.DATABASE_RXN, 
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))
   
   cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
   q = """select distinct rxcui, rxaui, atn, atv from 
       rxnsat where rxcui=%s and suppress='N' and 
       atn != 'NDC' order by rxaui, atn;"""
  
   cur.execute(q, (rxcui_id,))
   rows = cur.fetchall()
   
   graph.append(RDF.Statement(
                    ns['rxcui'][rxcui_id], 
                    ns['rdf']['type'], 
                    ns['rxcui']['']))
   
#   for row in rows:
#       atn = row['atn'].replace(" ", "_").encode()
#       
#       graph.append(RDF.Statement(
#                    ns['rxcui']['%s'%row['rxcui'].encode()], 
#                    ns['rxn']['has_RXAUI'], 
#                    ns['rxaui'][row['rxaui'].encode()] ))
#       
#       graph.append(RDF.Statement(
#                    ns['rxaui'][row['rxaui'].encode()], 
#                    ns['rxatn'][atn], 
#                    literal(row['atv'].encode()) ))

   q = """select min(rela) as rela, min(str) as str from 
           rxnrel r join rxnconso c on r.rxcui1=c.rxcui 
           where rxcui2=%s group by rela;"""
   
   cur.execute(q, (rxcui_id,))
   
   rows = cur.fetchall()
   for row in rows:
       graph.append(RDF.Statement(
                        ns['rxcui'][rxcui_id], 
                        ns['rxrel'][row['rela'].encode()], 
                        literal(row['str'].encode()) ))

   return

def strip_ns(target, ns):
    print target, ns
    return str(target.uri).split(ns)[1]

def update_store(permanent_store, new_data):
    for s in new_data:
        print s
        if not permanent_store.contains_statement(s):
            permanent_store.append(s)

def x_domain(r):
  ui = settings.SMART_UI_SERVER_LOCATION
  r['Access-Control-Allow-Origin'] = ui#"*"# "%s://%s:%s"%(ui['scheme'], ui['host'], ui['port'])
  return r


def trim(p, n):
    return '/'.join(p.split('/')[:-n]).encode()

def url_request(url, method, headers, data=None):
    (scheme, url) = url.split("://")

    domain = url.split("/")[0]
    path = "/"+"/".join(url.split("/")[1:])
    conn = None
    
    if (scheme == "http") :        
        conn = httplib.HTTPConnection(domain)
    elif (scheme == "https"):
        conn = httplib.HTTPSConnection(domain)

    if (method == "GET"):
        path += "?%s"%data
        data = None

    print "URL_REQUEST:", domain, method, path, data, headers        
    conn.request(method, path, data, headers)
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
       deleted.append(r)
       record_connector.pending_removes.append(r)
       
    if (save): record_connector.execute_transaction()
       
    return rdf_response(serialize_rdf(deleted))

def rdf_post(record_connector, new_g):
    for s in new_g:
        record_connector.pending_adds.append(s)

    record_connector.execute_transaction()
    return rdf_response(serialize_rdf(new_g))


logging.basicConfig(
      level = logging.DEBUG,
      format = '%(asctime)s %(levelname)s %(message)s',
      )
