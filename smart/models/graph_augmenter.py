from smart.common.util import URIRef, Literal, sp, rdf, default_ns
from smart.lib.utils import smart_path

def augment_data(g):
    # Quick and dirty CodedValue augmentation to start. 
    # TODO: generalize this mechanism to allow plug-in extensibility!
    
    code_q = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX sp: <http://smartplatforms.org/terms#>
            SELECT ?c
            WHERE { ?cv rdf:type sp:CodedValue .
                    ?cv sp:code ?c. }"""
        
    codes = set(g.query(code_q))
    print "queried ", code_q, codes
    codes = filter(lambda s: type(s) == URIRef and \
                           not str(s).startswith("urn:smart_external_id:") and \
                       not str(s).startswith(smart_path("")), codes)
    
    # For any URI nodes referencing external vocabularies...
    for c in codes:
        augment_code_uri(g,c)


code_map = [
    "http://rxnav.nlm.nih.gov/REST/rxcui?idtype=NUI&id=",
    "http://rxnav.nlm.nih.gov/REST/rxcui/",
    "http://www.ihtsdo.org/snomed-ct/concepts/",
    "http://fda.gov/UNII/"]

def augment_code_uri(g,c):
    g.add((c, rdf.type, sp.Code))
    for v in code_map:
        try:
            assert str(c).startswith(v), "Not a %s: %s"%(v, str(c))
            i = str(c)[len(v):]
            g.add((c, sp.system, URIRef(v)))
            g.add((c, default_ns['dcterms'].identifier, Literal(i)))
            print "Augmented with", v, i
            return
        except: continue
    

