from smart.common.util import URIRef, Literal, sp, rdf, default_ns, get_property
from smart.lib.utils import smart_path
from smart.common.rdf_ontology import ontology

def augment_data(g, var_bindings, new_nodes):
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


    # Attach each data element (med, problem, lab, etc), to the 
    # base record URI with the sp:hasDataElement predicate.
    recordURI = URIRef(smart_path("/records/%s"%var_bindings['record_id']))
    for n in new_nodes:
        node_type = get_property(g, n, rdf.type)

        # Make sure this is a "medical data element" type
        t = ontology[node_type]
        if (t.base_path == None): continue
        if (not t.base_path.startswith("/records")): continue
        if (n == recordURI): continue # don't assert that the record has itself as an element

        g.add((recordURI, sp.hasMedicalDataElement, n))


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
    

