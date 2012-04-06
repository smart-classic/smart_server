"""
Experimental support for the stardog triplestore.  
"""
from base import *

class StardogConnector(object):
    def __init__(self, endpoint=None):
        self.context = None
        self.pending_removes = ConjunctiveGraph()
        self.pending_adds = ConjunctiveGraph()
        self.pending_clears = []
        self.endpoint = endpoint or settings.TRIPLESTORE['record_endpoint']
        
        user = settings.TRIPLESTORE['username']
        password = settings.TRIPLESTORE['password']

        self.auth = "Basic "+base64.b64encode("%s:%s"%(user, password))
 

    def _request(self, url, method, headers=None, data=None):
        if headers == None: 
            headers = {}

        if "Authorization" not in headers:
            headers["Authorization"] = "Basic "+base64.b64encode("admin:admin")

        #print url, method, headers, data 
        return utils.url_request(url, method, headers, data)

    def add_conjunctive_graph(self, cg):
        return replace_conjunctive_graph(cg, drop=False)

    def clear_context(self, c):
        self.pending_clears.append(c)

    def replace_conjunctive_graph(self, cg, drop=True):
        drops = []
        inserts = []
        for g in cg.contexts():
            c = self.pending_adds.get_context(g.identifier)
            c += g
            if drop:
                self.clear_context(g.identifier)

    def sparql(self, q):
        u = self.endpoint+"/query"
        st = time.time()
        print "Querying, "#,q
        
        data = urllib.urlencode({"query" : q})
        s = time.time()

        accept = "application/rdf+xml, application/sparql-results+json"

        res = self._request(u, "POST", {"Content-type": "application/x-www-form-urlencoded", 
                                        "Accept" : accept}, data)
        print "results in ", (time.time() - st)#,res
        return res
            
    def _transaction_step(self, graph, url):
        if isinstance(graph.identifier, URIRef):
            param = urllib.urlencode({"graph-uri": (graph.identifier)})
            url = url + "?" + param
        data = graph.serialize(format="xml")
        self._request(url, "POST", {"Content-type": "application/rdf+xml"}, data)

    def _clear_transaction(self):
        self.pending_adds.remove((None,None,None)) 
        self.pending_removes.remove((None,None,None)) 
        self.pending_clears = []
        self.tx = None

    def transaction_begin(self):
        self._clear_transaction()
        self.tx = self._request(self.endpoint+"/transaction/begin", "POST")

    def transaction_commit(self):
        assert self.tx, "Can't commit a transaction that doesn't exist"

#        print "Clearing linked uris", len(self.pending_clears)
        for clearuri in self.pending_clears:
            self._request(self.endpoint+"/%s/clear?%s"%(self.tx, urllib.urlencode({"graph-uri": str(clearuri)})), "POST")
        
        for g in self.pending_adds.contexts():
            self._transaction_step( graph=g, url=self.endpoint+"/%s/add"%self.tx )

        for g in self.pending_removes.contexts():
            self._transaction_step( graph=g, url=self.endpoint+"/%s/remove"%self.tx )

        endtx = self._request(self.endpoint+"/transaction/commit/%s"%self.tx, "POST")
        print "committed tx", self.tx
        self._clear_transaction()
        return True

    def get_clinical_statement_uris(self, obj, limit_to_statements=None, **kwargs):
        q = """prefix : <http://smartplatforms.org/terms#>
               select distinct ?g ?g2 where {
                $unions
            }"""

        u = """graph $record {
                     $record :hasStatement ?g.
                }
                graph ?g {
                    $namedobject a """+obj.node.n3()+""".
                    optional {
                       ?g ?p ?g2.
                       graph ?g2 {
                           ?g2HACK a ?sttype. filter(?g2HACK = ?g2)
                            filter (?sttype != :MedicalRecord)
                       }
                    }
                }
            """
            
        if limit_to_statements:
            us = "{" + "}{".join([        
                u.replace("$namedobject", x.n3()) for x in limit_to_statements
            ])+ "}"
        else:
            us = u.replace("$namedobject", "?g")

        q = q.replace("$unions", us)

        results = self.select(q)
        ret =set([item for binding in results for item in binding.values() ])
        return ret

    def get_contexts(self, bindings):
        q = """    PREFIX : <http://smartplatforms.org/terms#>
        CONSTRUCT{
            ?s ?p ?o. 
        }
        { {
            $unions
          }
        }"""

        repl = " } union { ".join([
        """
        GRAPH %s {
          ?s ?p ?o.
        }"""%b.n3() for b in bindings])

        q = q.replace("$unions", repl)
        return self.sparql(q)
       
connector = StardogConnector
