from django.conf import settings
from smart.common.rdf_tools.rdf_ontology import api_types
import re

def getCodes (codeStr):
    return codeStr.split("|")

class Filter ():
    def getQuery (self, query_params):
        pass

    def apply (self, triplestore, uris, query_params):
        query = self.getQuery (query_params)
        if query and len(query) > 0:
            results = triplestore.select(query)
            valid_uris = set([uri for binding in results for uri in binding.values() ])
            return set([uri for uri in uris if uri in valid_uris])
        else:
            return uris

class FilterVitals (Filter):
    
    def getEncounterTypeSparqlFragment (self, encounter_type):

        return """
                       ?v sp:encounter/sp:encounterType/sp:code ?c .
                       FILTER(?c=uri(<http://smartplatforms.org/terms/codes/EncounterType#%s>)) .
               """ % encounter_type
                    
    def getQuery (self, query_params):
        trigger = False
    
        q = """
            PREFIX sp:<http://smartplatforms.org/terms#>
            SELECT DISTINCT ?v ?e WHERE {
                ?v sp:encounter ?e .
            """
    
        if 'encounter_type' in query_params.keys():
            q += self.getEncounterTypeSparqlFragment(query_params['encounter_type'])
            trigger = True
        
        q += "}"
        
        if trigger:
            return q
        else:
            return None
        
class FilterLabs (Filter):
    
    def getLoincSparqlFragment (self, codes):
        codes_strings = ["?c = uri(<http://purl.bioontology.org/ontology/LNC/%s>)" % code for code in codes]
        codes_str = " ||\n".join(codes_strings)
        return  """
                    ?l sp:labName/sp:code ?c .
                    FILTER(%s) .
                """ % codes_str
                
    def getDateSparqlFragment (self, date_from):
        return  """
                    ?l sp:specimenCollected/sp:startDate ?d . 
                    FILTER(?d >= "%s") .
                """ % date_from
                    
    def getQuery (self, query_params):
        trigger = False
    
        q = """
            PREFIX sp:<http://smartplatforms.org/terms#>
            SELECT DISTINCT ?l WHERE {
            """
    
        if 'loinc' in query_params.keys():
            q += self.getLoincSparqlFragment(getCodes(query_params['loinc']))
            trigger = True
        
        if 'date_from' in query_params.keys():
            q += self.getDateSparqlFragment(query_params['date_from'])
            trigger = True
        
        q += "}"
        
        if trigger:
            return q
        else:
            return None
            
            
class Paginator (object):

    def __init__ (self, by_rdf_term):
        self.by_rdf_term = by_rdf_term

    def sortedList (self, urls, triplestore):
        codes_strings = ["?uri = uri(%s)" % x.n3() for x in urls]
        codes_str = " ||\n".join(codes_strings)
        q =  """PREFIX sp:<http://smartplatforms.org/terms#>
                PREFIX dcterms:<http://purl.org/dc/terms/>
                SELECT DISTINCT ?uri ?date WHERE{
                   ?uri %s ?date .
                   FILTER(%s)
                }""" % (self.by_rdf_term, codes_str)
                
        results = triplestore.select(q)
        results = sorted(results, key = lambda r: ''.join((r['date'].n3(),r['uri'].n3())), reverse = True)
        return [item['uri'] for item in results] 

    def parseParams (self, params):
        if 'limit' in params.keys():
            limit = int(params['limit'])
            if limit > 100:
                limit = 100
        else:
            limit = 50
        if 'offset' in params.keys():
            offset = int(params['offset'])
        else:
            offset = 0
        
        return limit, offset

    def apply (self, triplestore, uris, path, params, meta):
        meta['resultsReturned'] = len(uris)
        meta['totalResultCount'] = len(uris)
        return uris
        
class SimplePaginator (Paginator):

    def apply (self, triplestore, uris, path, params, meta):
        limit, offset = self.parseParams (params)
        if limit:
            selected_items = list(uris)
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
        else:
            return uris

class CompoundPaginator (Paginator):

    def __init__ (self, by_rdf_term, pattern, predicate):
        super(CompoundPaginator, self).__init__(by_rdf_term)
        self.pattern = pattern
        self.predicate = predicate

    def apply (self, triplestore, uris, path, params, meta):
        limit, offset = self.parseParams (params)
        if limit:
            selected_items = [r for r in uris if r.find(self.pattern) != -1]
            selected_items = self.sortedList(selected_items, triplestore)
            meta['totalResultCount'] = len(selected_items)
            selected_items = selected_items[offset: offset+limit]
            meta['resultsReturned'] = len(selected_items)
            meta['resultOrder'] = '("%s")' % '","'.join((x.n3() for x in selected_items))
            if (offset+limit < meta['totalResultCount']):
                params['offset'] = offset + limit
                args = "&".join(["%s=%s" % (k, params[k]) for k in params.keys()])
                meta['nextPageURL'] = "%s/%s?%s" % (settings.SITE_URL_PREFIX.strip("/"), path, args)
            
            if len(selected_items) == 0:
                return set()
            else:
                codes_strings = ["?a = uri(%s)" % x.n3() for x in selected_items]
                codes_str = " ||\n".join(codes_strings)
                    
                q =  """PREFIX sp:<http://smartplatforms.org/terms#>
                        SELECT DISTINCT ?a ?b WHERE{
                           ?a sp:%s ?b .
                           FILTER(%s)
                        }""" % (self.predicate, codes_str)
                        
                results = triplestore.select(q)
                selected_items = set([item for binding in results for item in binding.values() ])
                return set([item for item in uris if item in selected_items])
        else:
            return uris
        
def getTypeName (type_uri):

    # Try resolving the name through the ontology
    uri = re.search("<(.*)>", type_uri).group(1)
    for t in api_types:
        if str(t.uri) == uri:
            return str(t.name)
            
    # If not, fall back to basic pattern matching
    return re.search("<http://smartplatforms.org/terms#(.*)>", type_uri).group(1)
        
FILTERS = {
    'VitalSigns': FilterVitals,
    'LabResult': FilterLabs
}
    
PAGINATORS = {
    'Encounter': SimplePaginator("sp:startDate"),
    'Immunization': SimplePaginator("dcterms:date"),
    'LabResult': SimplePaginator("sp:specimenCollected/sp:startDate"),
    'Problem': SimplePaginator("sp:startDate"),
    'VitalSigns': CompoundPaginator("dcterms:date", "vital_signs", "encounter"),
    'Fulfillment': CompoundPaginator("dcterms:date", "fulfillments", "medication"),
    'Medication': CompoundPaginator("sp:startDate", "medications", "fulfillment")
}

def selectFilter (type_url):
    type = getTypeName(type_url)
    if type in FILTERS.keys():
        return FILTERS[type]()
    else:
        return Filter()

def selectPaginator (type_url):
    type = getTypeName(type_url)
    if type in PAGINATORS.keys():
        return PAGINATORS[type]
    else:
        return Paginator(None)
