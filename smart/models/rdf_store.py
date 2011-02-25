"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.common.util import URIRef, Literal, BNode
from smart.models.apps import *
from smart.models.accounts import *
from smart.models import PHA
from django.conf import settings
from string import Template
import urllib, uuid

class PHA_RDFStore(Object): 
  Meta = BaseMeta()
  PHA = models.ForeignKey(PHA, unique=True)
  triples = models.XMLField(schema_path="%s../schema/%s"%(settings.XSLT_STYLESHEET_LOC, "rdf.xsd"))

  def __unicode__(self):
    try:
        return 'RDF Store %s, for %s' % (self.id, self.principal)
    except:
        return 'RDF Store %s, for ?' % (self.id)

class SesameConnector(object):
    def __init__(self, endpoint):
        self.context = None
        self.pending_removes = []
        self.pending_adds = []
        self.pending_clears = []
        self.endpoint = endpoint

    def request(self, url, method, headers, data=None):
        return utils.url_request(url, method, headers, data)
        
    def sparql(self, q):
        u = self.endpoint
        #print "Querying, ", q
        data = urllib.urlencode({"query" : q})
        res = self.request(u, "POST", {"Content-type": "application/x-www-form-urlencoded", 
                                        "Accept" : "application/rdf+xml,  application/sparql-results+xml"}, data)
        return res
            
    def serialize_node(self, node):
        t = None

        if (type(node) == URIRef):
          t = "uri"
        elif (type(node) == BNode):
          t = "bnode"
        elif (type(node) == Literal):
          t = "literal"
        else:
          raise Exception("Unknown node type for %s"%node)          
        
        return "<%s><![CDATA[%s]]></%s>"%(t,str(node),t)


    def serialize_statement(self, st):
        return "%s %s %s"%(self.serialize_node(st[0]),
                           self.serialize_node(st[1]),
                           self.serialize_node(st[2]),
                           )

    
    def execute_transaction(self):
        t = '<?xml version="1.0"?>'
        t += "<transaction>\n"

        if len(self.pending_clears) > 0:
          t += """
          <clear>
          <contexts>
          %s
          </contexts>
          </clear>"""%"\n".join([self.serialize_node(c) for c in self.pending_clears])

        for a in self.pending_adds:
            t += "<add>%s</add>\n"%self.serialize_statement(a)

        for d in self.pending_removes:
            t += "<remove>%s</remove>\n"%self.serialize_statement(d)
        
        t += "</transaction>"
        u = "%s/statements"%self.endpoint
        success =  self.request(u, "POST", {"Content-Type" : "application/x-rdftransaction"}, t)
        if (success):
            self.pending_clears = []
            self.pending_adds = []
            self.pending_removes = []
            return True
        raise Exception("Failed to execute sesame transaction: %s"%t)
   
class ContextSesameConnector(SesameConnector):
    def __init__(self, endpoint, context):
        super(ContextSesameConnector, self).__init__(endpoint)
        self.context = context
        
    def serialize_statement(self, st):
        return "%s %s %s %s"%(
                              self.serialize_node(st[0]),
                              self.serialize_node(st[1]),
                              self.serialize_node(st[2]),
                              self.serialize_node(URIRef(self.context.encode()))
                             )
        
    def sparql(self, q):
        if (q.find("$context") == -1 ): raise Exception("NO CONTEXT FOR %s"%q)
        q = Template(q).substitute(context="<%s>"%self.context)
        return super(ContextSesameConnector, self).sparql(q)

    def destroy_triples(self):
        self.pending_clears.append(URIRef(self.context.encode()))
        self.execute_transaction()


class DemographicConnector(SesameConnector):
    def __init__(self):
        super(DemographicConnector, self).__init__(settings.RECORD_SPARQL_ENDPOINT)

class RecordStoreConnector(ContextSesameConnector):
    def __init__(self, record):
        super(RecordStoreConnector, self).__init__(settings.RECORD_SPARQL_ENDPOINT, 
                                                   "http://smartplatforms.org/records/%s"%record.id)

class TemporaryStoreConnector(ContextSesameConnector):
    def __init__(self):
        self.temp_id =str(uuid.uuid4()) 
        super(TemporaryStoreConnector, self).__init__(settings.TEMP_SPARQL_ENDPOINT, 
                                                   "http://smartplatforms.org/records/%s"%self.temp_id)
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.destroy_triples()
    
class PHAConnector(ContextSesameConnector):
    def __init__(self, request):
        pha = request.principal
        if not (isinstance(pha, PHA)):
            raise Exception("RDF Store only stores data for PHAs.")

        super(PHAConnector, self).__init__(settings.PHA_SPARQL_ENDPOINT, 
                                                   "http://smartplatforms.org/phas/%s"%pha.email)
