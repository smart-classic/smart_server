from django.conf import settings
import json
from smart.common.rdf_tools.rdf_ontology import api_types, SMART_Class, SMART_API_Call
import re

DEFAULT_LIMIT=100
MAX_LIMIT=100

def getCodes (codeStr):
    return codeStr.split("|")

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
                """ + str(clauses)
        
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

            assert keys_used==set('v'), \
                   "Expected only ONE selected term:  'v', a clinical statement URI"
           
            return result_uris
        else:
            return  candidate_uris

class Paginator (object):

    def __init__ (self, by_rdf_term):
        self.by_rdf_term = by_rdf_term

    def sortedList (self, urls, triplestore):
        codes_strings = ["?uri = uri(%s)" % x.n3() for x in urls]
        codes_str = " ||\n".join(codes_strings)
        q =  """PREFIX sp:<http://smartplatforms.org/terms#>
                PREFIX dcterms:<http://purl.org/dc/terms/>
                SELECT DISTINCT ?uri ?sortParam WHERE{
                   ?uri %s ?sortParam .
                   FILTER(%s)
                } order by desc(?sortParam)""" % (self.by_rdf_term, codes_str)
                
        results = triplestore.select(q)
        return [item['uri'] for item in results] 

    def parseParams (self, params):
        if 'limit' in params.keys():
            limit = int(params['limit'])
            if limit > MAX_LIMIT:
                limit = MAX_LIMIT
        else:
            limit = DEFAULT_LIMIT 

        if 'offset' in params.keys():
            offset = int(params['offset'])
        else:
            offset = 0
        
        return limit, offset

    def __call__ (self, triplestore, obj, uris, path, params, meta):
        meta['resultsReturned'] = len(uris)
        meta['totalResultCount'] = len(uris)
        return uris
        
class SimplePaginator (Paginator):
    def __call__ (self, triplestore, obj, uris, path, params, meta):
        limit, offset = self.parseParams (params)

        selected_items = list(uris)
        if selected_items:
            selected_items = self.sortedList(selected_items, triplestore)

        meta['totalResultCount'] = len(selected_items)
        selected_items = selected_items[offset: offset+limit]
        meta['resultsReturned'] = len(selected_items)
        meta['resultOrder'] = '("%s")' % '","'.join((x.n3() for x in selected_items))
        if (offset+limit < meta['totalResultCount']):
            params['offset'] = offset + limit
            args = "&".join(["%s=%s" % (k, params[k]) for k in params.keys()])
            meta['nextPageURL'] = "%s%s?%s" % (settings.SITE_URL_PREFIX, path, args)
        selected_items = set(selected_items)
        return selected_items

PAGINATORS = {}
FILTERS = {}
for c in SMART_API_Call.store.values():
    if c.filters:
        FILTERS[c.target] = FilterSet(c)
    if c.default_sort:
        PAGINATORS[c.target] = SimplePaginator(str(c.default_sort))
   
# TODO: Remove these and use default_dict instead of vanilla dicts 
#       for PAGINATORS, FILTERS
def selectFilter (type_url):
    try:
        return FILTERS[type_url]
    except:
        return FilterSet()

def selectPaginator (type_url):
    try:
        return PAGINATORS[type_url]
    except:
        return Paginator(None)
