"""
RDF Store for PHAs

Josh Mandel
"""

from smart.lib import utils
import RDF
from smart.lib.utils import parse_rdf
import uuid
import re

NS = utils.default_ns()
class RDFProperty(object):
    def __init__(self, predicate, object=None):
        self.predicate = predicate
        self.object = object

class RDFObject(object):
    def __init__(self, type=None, path=None):
        self.type = type
        self.path=path
        self.properties = [RDFProperty(predicate=NS['rdf']['type']), 
                           RDFProperty(predicate=NS['sp']['external_id'])]
        self.children = {}

    def find_parent(self, g, child):
        q_parent = RDF.Statement(subject=None, 
                            predicate=None, 
                            object=child)
        
        found=None

        for s in g.find_statements(q_parent):
            if (found): raise Exception("Found >1 parent for ", child)
            found = s.subject.uri
        return found

    def internal_id(self, record_connector, external_id):
        id_graph = parse_rdf(record_connector.sparql("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            CONSTRUCT {?s <http://smartplatforms.org/external_id> "%s".}
            FROM $context
            WHERE {?s <http://smartplatforms.org/external_id> "%s".
                   ?s rdf:type %s.
                  }
        """%(external_id, external_id, "<"+str(self.type.uri)+">")))
        
        l = list(id_graph)
        if len(l) > 1:
            raise Exception( "MORE THAN ONE ENTITY WITH EXTERNAL ID %s : %s"%(external_id, ", ".join([str(x.subject) for x in l])))
    
        try:
            s =  l[0].subject
            return str(s.uri).encode()   
        except: 
            return None

    
    def remap_node(self, model, old_node, new_node):
        for s in model.find_statements(RDF.Statement(old_node, None, None)):
            del model[s]
            model.append(RDF.Statement(new_node, s.predicate, s.object))
        for s in model.find_statements(RDF.Statement(None, None, old_node)):
            del model[s]
            model.append(RDF.Statement(s.subject, s.predicate, new_node))            
        return
    
    def path_to(self, child_type):
        to_strip = self.path.replace("{new_id}","")
        stripped = child_type.path.replace(to_strip, "")
        stripped = re.sub("^{.*?}", "", stripped)
        return stripped
    
    def determine_full_path(self, request_path, parent_path):
        if parent_path == None: # No parent in the supplied graph, so we just use the requess's path
                                # e.g. (/records/{rid}/medications/) to determine URIs
            if (request_path.endswith("/")): request_path += "{new_id}"
            match_string = re.sub("{.*?}", "(.*?)", self.path)
            request_path_ok = re.search(match_string, request_path).groups()
            assert(len(request_path_ok) > 0), "Expect request path to match child path"
            ret = request_path
            
        else: # a parent *was* supplied!  Just take the relative portion of this path.
            ret =  str(parent_path) + "/" + self.path.split("/")[-2] + "/{new_id}"
            
        ret = ret.replace("{new_id}", str(uuid.uuid4()))
        return ret.encode()
    
    def ensure_only_one_put(self, g):
        qs = RDF.Statement(subject=None, 
                   predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                   object=None)
    
        typed_object_count = 0
        errors = []
        for s in g.find_statements(qs):
            typed_object_count += 1
            errors.append(str(s.object))
        assert typed_object_count == 1, "You must PUT exactly one typed resource at a time; you tried putting %s: %s"%(typed_object_count, ", ".join(errors))
    
        return
    
    def generate_uris(self, g, request_path):   
        if (self.type == None): return 
    
        q_typed_nodes = RDF.Statement(subject=None, 
                                      predicate=RDF.Node(uri_string='http://www.w3.org/1999/02/22-rdf-syntax-ns#type'), 
                                      object=self.type)
    
        node_map = {}    
        for s in g.find_statements(q_typed_nodes):
            if s.subject not in node_map:
                parent_path = self.find_parent(g, s.subject)
                full_path =  self.determine_full_path(request_path, parent_path)                
                node_map[s.subject] = RDF.Node(uri_string=full_path)

        for (old_node, new_node) in node_map.iteritems():
            self.remap_node(g, old_node, new_node)

        for c in self.children.values():
            c.generate_uris(g, request_path)

        return node_map.values()

    def types_to_map(self, level=0):
        ret = {}
        
        if (self.type != None):
                ret[self.type] = self.path
                
        for (crel, c) in self.children.iteritems():
            for (k,v) in c.types_to_map(level+1).iteritems():
                ret[k] = v

        return ret

    def typed(self, level=0):
        if (self.type == None): return ""
        name = self.leveled("?s", level)
        return " " + name + " rdf:type <"+str(self.type.uri)+">. "
    
    def leveled(self, val, level=0):
        if level == 0: return val
        return val + "_"+str(level)
    
    def id_filter(self, id=None):
        if (id != None): return "FILTER (?s=" + id + ") "
        return ""
        
    def insertions(self, id=None, level=1, parent_clause="", restrict_to_child_types=None):
        ret = []
        
        this_level = parent_clause
        this_level += self.typed()
        
        if (id != None):
            ret.append("?s ?p ?o FILTER (?o="+id+")")
            this_level += self.id_filter(id)
            
        if (level == 1): 
            parent_clause = this_level
            parent_clause = parent_clause.replace("?s ", "?s_1 ") 
            parent_clause = parent_clause.replace("?s=", "?s_1=") 

        this_level += "?s ?p ?o.  FILTER (" + " || ".join([self.leveled("?p")+"=<"+str(p.uri)+">" for p in [x.predicate for x in self.properties]  + self.children.keys()])+")"

        if (restrict_to_child_types == None or restrict_to_child_types == self.type):      
            restrict_to_child_types = None
            ret.append(this_level)
        
        for (rel, c) in self.children.iteritems():
            next_parent_clause = parent_clause.replace("?s.", self.leveled("?s", level) + ".") + self.leveled("?s", level) + " <"+str(rel.uri)+"> ?s. "
            ret.extend(c.insertions(level=level+1, parent_clause=next_parent_clause, restrict_to_child_types=restrict_to_child_types)) 
            
        return ret
    
    def query_one(self, id, restrict=None):
        return self.query_all(id=id, restrict=restrict)
        
    def query_all(self, id=None,level=0, restrict=None):
        ret = """
        BASE <http://smartplatforms.org/>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        CONSTRUCT {?s ?p ?o.}
        FROM $context
        WHERE {
           { $insertion_point } 
        }
        """

        insertions = self.insertions(id=id, restrict_to_child_types=restrict)
        ret = ret.replace("$insertion_point", " } UNION { ".join(insertions))
        
        return ret

prescriber = RDFObject()
prescriber.properties.extend([RDFProperty(NS['dcterms']['title']),
                              RDFProperty(NS['sp']['NPI']),
                              RDFProperty(NS['sp']['DEA'])])

vcard = RDFObject()
vcard.properties.append(RDFProperty(NS['v']['street-address']))
vcard.properties.append(RDFProperty(NS['v']['locality']))
vcard.properties.append(RDFProperty(NS['v']['postal-code']))
vcard.properties.append(RDFProperty(NS['v']['country-name']))

pharmacy = RDFObject()
pharmacy.properties.append(RDFProperty(NS['dcterms']['title']))
pharmacy.properties.append(RDFProperty(NS['sp']['NCPDPID']))
pharmacy.children[NS['v']['adr']] = vcard

fill = RDFObject(type=NS['sp']['fulfillment'], path="http://smartplatforms.org/records/{record_id}/medications/{medication_id}/fulfillments/{new_id}")
fill.properties.append(RDFProperty(NS['dc']['date']))
fill.properties.append(RDFProperty(NS['sp']['PBM']))
fill.properties.append(RDFProperty(NS['sp']['dispenseQuantity']))
fill.properties.append(RDFProperty(NS['sp']['dispenseUnits']))
fill.properties.append(RDFProperty(NS['sp']['dispenseDaysSupply']))
fill.children[NS['sp']['prescriber']] = prescriber
fill.children[NS['sp']['pharmacy']] = pharmacy

med = RDFObject(type=NS['sp']['medication'], path="http://smartplatforms.org/records/{record_id}/medications/{new_id}")
med.properties.append(RDFProperty(NS['dcterms']['title']))
med.properties.append(RDFProperty(NS['med']['drug']))
med.properties.append(RDFProperty(NS['med']['dose']))
med.properties.append(RDFProperty(NS['med']['doseUnit']))
med.properties.append(RDFProperty(NS['med']['strength']))
med.properties.append(RDFProperty(NS['med']['strengthUnit']))
med.properties.append(RDFProperty(NS['med']['frequency']))
med.properties.append(RDFProperty(NS['med']['route']))
med.properties.append(RDFProperty(NS['med']['instructions']))
med.properties.append(RDFProperty(NS['med']['startDate']))
med.properties.append(RDFProperty(NS['med']['endDate']))
med.children[fill.type] = fill

allergen = RDFObject()
allergen.properties.append(RDFProperty(NS['allergy']['category']))
allergen.properties.append(RDFProperty(NS['allergy']['substance']))
allergen.properties.append(RDFProperty(NS['dcterms']['title']))

allergy = RDFObject(type=NS['sp']['allergy'], path="http://smartplatforms.org/records/{record_id}/allergies/{new_id}")
allergy.properties.append(RDFProperty(NS['allergy']['severity']))
allergy.properties.append(RDFProperty(NS['allergy']['reaction']))
allergy.children[NS['allergy']['allergen']] = allergen

problem = RDFObject(type=NS['sp']['problem'], path="http://smartplatforms.org/records/{record_id}/problems/{new_id}")
problem.properties.append(RDFProperty(NS['dcterms']['title']))
problem.properties.append(RDFProperty(NS['snomed-ct']['concept']))
problem.properties.append(RDFProperty(NS['sp']['onset']))
problem.properties.append(RDFProperty(NS['sp']['resolution']))
problem.properties.append(RDFProperty(NS['sp']['notes']))

demographic = RDFObject(type=NS['foaf']['Person'],  path="http://smartplatforms.org/records/{record_id}/demographics")
demographic.properties.append(RDFProperty(NS['foaf']['givenName']))
demographic.properties.append(RDFProperty(NS['foaf']['familyName']))
demographic.properties.append(RDFProperty(NS['foaf']['gender']))
demographic.properties.append(RDFProperty(NS['spdemo']['zipcode']))
demographic.properties.append(RDFProperty(NS['spdemo']['birthday']))

foafPerson = RDFObject()
foafPerson.properties.append(RDFProperty(NS['foaf']['name']))

foafOrganization = RDFObject()
foafOrganization.properties.append(RDFProperty(NS['foaf']['name']))

provider = RDFObject()
provider.children[NS['foaf']['Person']] = foafPerson
provider.children[NS['foaf']['Organization']] = foafOrganization

note = RDFObject(type=NS['sp']['note'], path="http://smartplatforms.org/records/{record_id}/notes/{new_id}")
note.properties.append(RDFProperty(NS['sp']['dayOfVisit']))
note.properties.append(RDFProperty(NS['sp']['notes']))
note.children[NS['sp']['provider']] = provider
