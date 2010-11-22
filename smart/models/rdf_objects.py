import re, RDF, os, uuid
from smart.models.rdf_store import RecordStoreConnector
from smart.models.records import Record
from smart.lib.utils import default_ns, trim, smart_base, smart_parent, smart_path, smart_external_path, rdf_get, rdf_post, rdf_delete, parse_rdf, serialize_rdf
from django.conf import settings
from rdf_rest_operations import *

NS = default_ns()
sp  = RDF.NS("http://smartplatforms.org/")
rdf = RDF.NS('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
owl = RDF.NS("http://www.w3.org/2002/07/owl#")
rdfs = RDF.NS("http://www.w3.org/2000/01/rdf-schema#")


class RDFProperty(object):
    def __init__(self, predicate, object=None):
        self.predicate = predicate
        self.object = object

class RDFObject(object):
    def __init__(self, type=None, path=None):
        self.type = type
        self.path=path
        self.parent = None
        self.properties = [RDFProperty(predicate=str(NS['rdf']['type'].uri)), 
                           RDFProperty(predicate=str(NS['sp']['external_id'].uri))]
        self.children = {}
        self.get_one = record_get_object
        self.get_all = record_get_all_objects
        self.delete_one = record_delete_object
        self.delete_all = record_delete_all_objects
        self.post = record_post_objects
        self.put = record_put_object

    
    def type_node(self):
        return RDF.Node(uri_string=self.type)

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
        """%(external_id, external_id, "<"+self.type+">")))
        
        l = list(id_graph)
        if len(l) > 1:
            raise Exception( "MORE THAN ONE ENTITY WITH EXTERNAL ID %s : %s"%(external_id, ", ".join([str(x.subject) for x in l])))
    
        try:
            s =  l[0].subject
            return str(s.uri).encode()   
        except: 
            return None

    
    def remap_node(self, model, old_node, new_node):
        for s in list(model.find_statements(RDF.Statement(old_node, None, None))):
            del model[s]
            model.append(RDF.Statement(new_node, s.predicate, s.object))
        for s in list(model.find_statements(RDF.Statement(None, None, old_node))):
            del model[s]
            model.append(RDF.Statement(s.subject, s.predicate, new_node))            
        return
    
    def path_to(self, child_type):
        stripped = child_type.path.replace(self.path, "")
        stripped = re.sub("{.*?}", "", stripped)
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
                                      object=self.type_node())
    
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

    def typed(self, level=0):
        if (self.type == None): return ""
        name = self.leveled("?s", level)
        return " " + name + " rdf:type <"+self.type+">. "
    
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

        # If we're only interested in querying, e.g. fills that belong to a medication
        # We should still recurse down the type hierachy starting at meds -- but
        # don't actually CONSTRUCT any triples unless/until we get to a fill object.
        predicates_to_capture = [restrict_to_child_types]
        if (restrict_to_child_types == None or restrict_to_child_types == self.type):      
            restrict_to_child_types = None
            predicates_to_capture = [x.predicate for x in self.properties]  + self.children.keys() 

        this_level += "?s ?p ?o.  FILTER (" + " || ".join(["?p=<"+p+">" for p in predicates_to_capture])+")"
        ret.append(this_level)
        
        for (rel, c) in self.children.iteritems():
            next_parent_clause = parent_clause.replace("?s.", self.leveled("?s", level) + ".") + self.leveled("?s", level) + " <"+rel+"> ?s. "
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