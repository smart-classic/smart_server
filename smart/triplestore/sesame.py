from base import *


class SesameConnector(object):
    def __init__(self, endpoint=None):
        self.context = None
        self.pending_removes = ConjunctiveGraph()
        self.pending_adds = ConjunctiveGraph()
        self.pending_clears = []
        self.endpoint = endpoint or settings.TRIPLESTORE['record_endpoint']

    def _sesame_serialize_node(self, node):
        t = None

        if (type(node) == URIRef):
            t = "uri"
        elif (type(node) == BNode):
            t = "bnode"
        elif (type(node) == Literal):
            t = "literal"
        else:
            raise Exception("Unknown node type for %s" % node)

        return "<%s><![CDATA[%s]]></%s>" % (t, str(node), t)

    def _sesame_serialize_statement(self, st):
        return "%s %s %s" % (
            self._sesame_serialize_node(st[0]),
            self._sesame_serialize_node(st[1]),
            self._sesame_serialize_node(st[2]),
        )

    def _serialize_flat(self, g):
        return "\n     ".join([" ".join(map(lambda x: x.n3(), s)) + "." for s in g])

    def _request(self, url, method, headers, data=None):
        return utils.url_request(url, method, headers, data)

    def add_conjunctive_graph(self, cg):
        return self.replace_conjunctive_graph(cg, drop=False)

    def clear_context(self, c):
        self.pending_clears.append(c)

    def replace_conjunctive_graph(self, cg, drop=True):
        for g in cg.contexts():
            #print 'g is: ' + g.identifier
            c = self.pending_adds.get_context(g.identifier)
            c += g
            if drop:
                self.clear_context(g.identifier)

    def sparql_update(self, q):
        u = self.endpoint + "/statements"
        st = time.time()
        print "Updating", len(q)
        res = self._request(
            u,
            "POST",
            {"Content-type": "application/x-www-form-urlencoded"},
            urllib.urlencode({"update": q})
        )
        print "results in ", (time.time() - st)  # , res
        return res

    def sparql(self, q):
        u = self.endpoint
        st = time.time()
        #print "Querying, ",q

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "application/rdf+xml, application/sparql-results+json"
        }
        data = urllib.urlencode({"query": q})
        try:
            res = self._request(u, "POST", headers, data)
            #print "results in ", (time.time() - st)
            return res
        except Exception, e:
            pass
        return None

    def _clear_transaction(self):
        self.pending_adds.remove((None, None, None))
        self.pending_removes.remove((None, None, None))
        self.pending_clears = []
        self.tx = False

    def transaction_begin(self):
        self._clear_transaction()
        self.tx = True

    def transaction_commit(self):
        assert self.tx, "Can't commit a transaction that wasn't initiated"

        drops = []
        for c in self.pending_clears:
            drops.append("DROP GRAPH %s;\n" % c.n3())
        if len(drops) > 0:
            self.sparql_update("\n".join(drops))

        for g in self.pending_adds.contexts():
            q = "INSERT DATA { GRAPH %s {\n     %s }}" % (g.identifier.n3(), self._serialize_flat(g))
            self.sparql_update(q)

        for g in self.pending_removes.contexts():
            q = "DROP DATA { GRAPH %s {\n     %s } }" % (g.identifier.n3(), self._serialize_flat(g))
            self.sparql_update(q)

        self._clear_transaction()

    def get_clinical_statement_uris(self, obj):
        q = """prefix : <http://smartplatforms.org/terms#>
               select distinct ?g  where {
                graph $record {
                     $record :hasStatement ?g.
                }
                {
                    graph ?g {
                       ?g a """ + obj.node.n3() + """.
                    }
                }
            }"""

        results = self.select(q)
        ret = set([item for binding in results for item in binding.values()])

        return ret

    def expand_to_neighboring_statements(self, limit_to_statements):
        q = """prefix : <http://smartplatforms.org/terms#>
               select distinct ?g ?g2 where {
                graph $record {
                     $record :hasStatement ?g.
                } OPTIONAL {
                      graph ?g {?g ?p ?g2.}
                      graph ?g2 {?g2 a ?g2type.}
                      filter(?g2type != :MedicalRecord)
                   }
            }"""
        if limit_to_statements:
            q += """ BINDINGS ?g {(""" + ")(".join([
                x.n3() for x in limit_to_statements
            ]) + """)} """

        results = self.select(q)
        ret = set([item for binding in results for item in binding.values()])

        return ret

    def get_contexts(self, bindings):

        if len(bindings) == 0:
            g = ConjunctiveGraph()
            return g.serialize(format="xml")

        q = """    PREFIX : <http://smartplatforms.org/terms#>
        CONSTRUCT{
            ?s ?p ?o.
        }
        {
            GRAPH ?g {
              ?s ?p ?o.
            }
        }"""

        q += """ BINDINGS ?g {(""" + ")(".join([
            x.n3() for x in bindings
        ]) + """)} """

        return self.sparql(q)


connector = SesameConnector
