"""
Triple store interface for SMART

Josh Mandel
"""

from base import *

from filters import runFiltering, runPagination

engine = "smart.triplestore.%s"%settings.TRIPLESTORE['engine']
__import__(engine)
engine = sys.modules[engine]

class TripleStore(engine.connector):
    def __init__(self, endpoint=None):
        super(TripleStore, self).__init__(settings.TRIPLESTORE['record_endpoint']) 

    def add_conjunctive_graph(self, cg):
        return super(TripleStore, self).add_conjunctive_graph(cg)

    def replace_conjunctive_graph(self, cg, drop=True):
        return super(TripleStore, self).replace_conjunctive_graph(cg, drop)

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

    def get_objects(self, path, queries, obj, limit_to_statements=None):
        timeStart = time.time()
        meta = {}
   
        matches = super(TripleStore, self).get_clinical_statement_uris(obj)

        if matches:
            matches = runFiltering (self, obj, matches, queries)
            if (limit_to_statements):
                meta['totalResultCount'] = len(set(matches) & set(limit_to_statements))
            else:
                meta['totalResultCount'] = len(matches)
        print "filtered", len(matches)

        if matches:
            matches = runPagination (self, obj, matches, queries, path, meta)
            if (limit_to_statements):
                meta['resultsReturned'] = len(set(matches) & set(limit_to_statements))
            else:
                meta['resultsReturned'] = len(matches)
        print "paged", len(matches)

        if matches:
            matches = super(TripleStore, self).expand_to_neighboring_statements(limit_to_statements or matches)
        print "expanded", len(matches)

        if not matches:
            return Graph().serialize(format="xml")

        res = self.get_contexts(matches)
        meta['processingTimeMs'] = int((time.time() - timeStart) * 1000)
        
        return self.addResponseSummary(res, meta)
        
    def addResponseSummary (self, rdfxml, meta):
        g = parse_rdf(rdfxml)

        rsNode = BNode()
        g.add((rsNode,RDF.type,NS['api']['ResponseSummary']))
        
        for key in meta.keys():
            if type(meta[key]) == list:
                bn = BNode()
                g.add((rsNode,NS['api'][key],bn))
                Collection(g, bn, meta[key])
            else:
                g.add((rsNode,NS['api'][key],Literal(meta[key])))
        
        return g.serialize(format="xml")

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
