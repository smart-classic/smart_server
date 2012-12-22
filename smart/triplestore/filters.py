from collections import defaultdict
from django.conf import settings
from smart.common.rdf_tools.rdf_ontology import SMART_API_Call

class SparqlClause(list):
    pass

class AndClause(SparqlClause):
    def __str__(self):
        return "{"+"}\n{".join([str(x) for x in self])+"}"

class OrClause(SparqlClause):
    def __str__(self):
        return "{"+"}\nUNION\n{".join([str(x) for x in self])+"}"

class FilterSet(object):
    def __init__(self, smart_type=None):
        self.smart_type = smart_type
        self.filters = []
        if smart_type:
            self.filters = smart_type.filters

    def sub(self, f, k, v):
        return f.filter_sparql.replace("{"+k+"}", v)

    def getQuery(self, query_params):
        clauses = AndClause()
        
        for f in self.filters:
            k = f.client_parameter_name
            if k in query_params:
                o = OrClause()
                vv = query_params[k]
                for v in vv.split("|"): 
                    o.append(self.sub(f, k, v))
                clauses.append(o)

        if clauses:
            return """
                PREFIX sp:<http://smartplatforms.org/terms#>
                PREFIX dcterms:<http://purl.org/dc/terms/>
                SELECT ?v
                {%s}
                """ % str(clauses)
        
        return None

    def __call__(self, triplestore, candidate_uris, query_params):
        query = self.getQuery (query_params)
        if query:
            query += """ BINDINGS ?v {("""+")(".join([
                        x.n3() for x in candidate_uris
                    ])+""")} """

            results = triplestore.select(query)
            keys_used = set()
            result_uris = set()
            for v in results:
                keys_used |= (set(v.keys()))
                result_uris |= (set(v.values()))

            assert not keys_used or keys_used==set('v'), \
                   "Expected only ONE selected term:  'v', a clinical statement URI"

            return result_uris
        else:
            return  candidate_uris

class Paginator (object):

    def __init__ (self, by_rdf_term):
        self.by_rdf_term = by_rdf_term

    def sortedList (self, triplestore, uris):
        if uris:
            filter_str = " ||\n".join(["?uri = uri(%s)" % x.n3() for x in uris])
            q =  """PREFIX sp:<http://smartplatforms.org/terms#>
                    PREFIX dcterms:<http://purl.org/dc/terms/>
                    SELECT DISTINCT ?uri ?sortParam WHERE{
                       ?uri %s ?sortParam .
                       FILTER(%s)
                    } ORDER BY DESC (?sortParam) ASC (?uri)""" % (self.by_rdf_term, filter_str)

            results = triplestore.select(q)
            return [item['uri'] for item in results]
        else:
            return []

    def parseParams (self, params):
        try:
            limit = int(params['limit'])
            if settings.MAX_PAGE_LIMIT:
                limit = min(limit, settings.MAX_PAGE_LIMIT)
        except:
            limit = settings.DEFAULT_PAGE_LIMIT 

        try:
            offset = int(params['offset'])
        except:
            offset = 0
        
        return limit, offset

    def __call__ (self, triplestore, candidate_uris, params, path, meta):
        return candidate_uris
        
class SimplePaginator (Paginator):
    def __call__ (self, triplestore, candidate_uris, params, path, meta):
        limit, offset = self.parseParams (params)
        if limit:
            sorted_uris = self.sortedList(triplestore, candidate_uris)
            page_uris = sorted_uris[offset: offset+limit]
            meta['resultOrder'] = page_uris
            if (offset+limit < len(sorted_uris)):
                params['offset'] = offset + limit
                params['limit'] = limit
                args = "&".join(["%s=%s" % (k, params[k]) for k in params.keys()])
                meta['nextPageURL'] = "%s%s?%s" % (settings.SITE_URL_PREFIX, path, args)
            return set(page_uris)
        else:
            return super(SimplePaginator, self).__call__(triplestore, candidate_uris, params, path, meta)

PAGINATORS = defaultdict(lambda:Paginator(None))
FILTERS = defaultdict(lambda:FilterSet())

for c in SMART_API_Call.store.values():
    if c.filters:
        FILTERS[c.target] = FilterSet(c)
    if c.default_sort:
        PAGINATORS[c.target] = SimplePaginator(str(c.default_sort))
   
def runFiltering (triplestore, obj, uris, query_params):
    f = FILTERS[obj.node]
    return f(triplestore, uris, query_params)
        
def runPagination (triplestore, obj, uris, query_params, path, meta):
    param_dict = {}
    for k in query_params:
       param_dict[k] = query_params[k]
    p = PAGINATORS[obj.node]
    return p(triplestore, uris, param_dict, path, meta)