"""
Triple store interface for SMART

Josh Mandel
"""

from smart.lib import utils
from smart.common.rdf_tools.util import URIRef, Literal, BNode
from rdflib import Graph, ConjunctiveGraph
from django.conf import settings
import urllib, uuid, base64
import json
import sys

engine = "smart.triplestore.%s"%settings.TRIPLESTORE['engine']
__import__(engine)
engine = sys.modules[engine]

class TripleStore(engine.connector):
    def __init__(self, endpoint=None):
        super(TripleStore, self).__init__(settings.TRIPLESTORE['record_endpoint']) 

    def add_conjunctive_graph(self, cg):
        return super(TripleStore, self).add_conjunctive_graph(cg)

    def replace_conjunctive_graph(self, cg):
        return super(TripleStore, self).replace_conjunctive_graph(cg)

    def remove_conjunctive_graph(self, cg):
        return super(TripleStore, self).remove_conjunctive_graph(cg)

    def transaction_begin(self):
        return super(TripleStore, self).transaction_begin()

    def transaction_commit(self):
        return super(TripleStore, self).transaction_commit()

    def clear_context(self, context):
        return super(TripleStore, self).clear_context(context)

    def sparql(self, query):
        return super(TripleStore, self).sparql(query)

    def select(self, q):
        r = self.sparql(q)
        #print "RES", r
        jr = json.loads(r)

        if "results" not in jr:
            return [] # TODO bug report to stardog

        for b in jr["results"]["bindings"]:
            for k,v in b.iteritems():
                if v["type"]=="uri":
                    b[k] = URIRef(v["value"])
                elif v["type"]=="literal":
                    b[k] = Literal(v["value"])
                elif v["type"]=="blank":
                    b[k] = BNode(v["value"])
                else:
                    raise "Unknown binding type for " + v

        return jr["results"]["bindings"]

    def destroy_context_and_neighbors(self, context):
        u = """
            select distinct ?o WHERE {
              graph """+context.n3()+""" {
                  ?s ?p ?o.
              }
            }"""
    
        bindings = self.select(u)
        neighbors =set([item for binding in bindings for item in binding.values() ])
        for n in neighbors:
            self.clear_context(n)

    def get_contexts(self, contexts):
        return super(TripleStore, self).get_contexts(contexts)

    def get_objects(self, obj, limit_to_statements=None):
        matches = super(TripleStore, self).get_clinical_statement_uris(obj, limit_to_statements)
        if not matches:
            return Graph().serialize(format="xml")
        return self.get_contexts(matches)

class ContextTripleStore(TripleStore):
    queryparam = "$context"

    def __init__(self, endpoint, context):
        super(ContextTripleStore, self).__init__(endpoint)
        self.context = URIRef( context )

    def sparql(self, q):
        q = q.replace(self.queryparam, self.context.n3())
        return super(ContextTripleStore, self).sparql(q)
  
class RecordTripleStore(ContextTripleStore):
    queryparam = "$record"

    def __init__(self, record):
        super(RecordTripleStore, self).__init__(settings.TRIPLESTORE['record_endpoint'], 
                                                   settings.SITE_URL_PREFIX + 
                                                        '/records/' +
                                                        record.id)
