from rdf_ontology import *
import json
import re

def node(uri):
    if uri.startswith("_:"):
        return BNode(uri[2:])
    elif uri.startswith('"'):
        return Literal(uri[1:-1])
    return URIRef(uri[1:-1])

def key_to_mongo(s):
    ret = ""
    if not isinstance(s, list):
        s = [s]

    for i in s:
        if hasattr(s, 'uri'):
            s = str(s.uri)
        ret += re.sub("\.", "&#46;", s)

    return ret

def key_from_mongo(s):
    return re.sub("&#46;", ".", s)


def jsoniri(n):
    if isinstance(n, BNode):
        return n.n3()
    else:
        return str(n)

class JSONifier(object):
    def __init__(self, graph):
        self.graph = graph
        self.statement_elements = {}
        self.context = {}
        self.subjects_added = {}
        self.JSONify()

    def JSONify(self):
        for t in api_types:

            if not t.is_statement and t.uri != sp.MedicalRecord: 
                continue

            nodes = map(lambda x: x[0], self.graph.triples((None, rdf.type, t.uri)))
            for n in nodes:
                self.add_statements(n)

    def add_statements(self, n):
        try:
            s = self.statement_elements[n]
            return
        except KeyError: pass

        thisnode = { 
            '@type': map(lambda x: jsoniri(x), 
                         get_property_list(self.graph, n, rdf.type))
            }
        t = SMART_Class[thisnode['@type'][0]]

        if t.is_statement or t.uri==sp.MedicalRecord:
            thisnode['@subject'] =  { '@iri':  jsoniri(n) }

        self.statement_elements[n] = thisnode
        for dp in t.data_properties:
            v = map(lambda x: x[2], self.graph.triples((n, dp.uri, None)))
            assert len(v) < 2 or dp.multiple_cardinality, "Cardinality mismatch %s %s"%(dp.uri, v)
                
            these = []
            for s in v: 
                these.append(s.n3()[1:-1])
            if len(these)==0: continue  

            dpkey = key_to_mongo(jsoniri(dp.uri))
            if dp.multiple_cardinality:
                thisnodet[dpkey] = these
            elif len(these)==1:
                thisnode[dpkey] = these[0]

        for op in t.object_properties:
            v = map(lambda x: x[2], self.graph.triples((n, op.uri, None)))
            assert len(v) < 2 or op.multiple_cardinality, "Cardinality mismatch %s %s"%(op.uri, v)

            these = []
            for s in v: 
                self.add_statements(s)
                if op.to_class.is_statement or op.to_class.uri==sp.MedicalRecord:
                    these.append({"@iri":  jsoniri(s)})
                else:
                    these.append(self.statement_elements[s])
                    del self.statement_elements[s]
            if len(these)==0: continue
            opkey = key_to_mongo(jsoniri(op.uri))
            if op.multiple_cardinality:
                thisnode[opkey] = these
            elif len(these)==1:
                thisnode[opkey] = these[0]
        return

class RDFifier(object):
    def __init__(self, jsdata):
        self.graph =  bound_graph()

        if not isinstance(jsdata, list):
            jsdata = [jsdata]
        self.jsdata = jsdata

        for item in self.jsdata:
            self.rdf_item(item)

    def rdf_item(self, item):
        if isinstance(item, list):
            return [self.rdf_item(x) for x in item]

        if isinstance(item, str) or isinstance(item, unicode):
            return Literal(item)

        item_node = BNode()
        try:  # what is a cleaner pattern for multiple attempts?
            item_node = URIRef(item["@subject"]["@iri"])
        except:
            try:
                item_node = URIRef(item["@iri"])
            except: pass

        item_type = None
        try:
            item_type = item["@type"]
        except: pass

        if item_type:
            if  not isinstance(item_type, list):
                item_type = [item_type]
            for t in item_type:
                self.graph.add((item_node, rdf.type, URIRef(t)))
        
        for k, v in item.iteritems():
            if k[0] in ["@", "_"]: # don't add @type, @iri, @subject, _id
                continue

            k = key_from_mongo(k)
            subitem_nodes = self.rdf_item(v)
            if not isinstance(subitem_nodes, list):
                subitem_nodes = [subitem_nodes]
            for n in subitem_nodes:
                self.graph.add((item_node, URIRef(k), n))

        return item_node

def readall():
    ts =  datetime.datetime.now()

    record = sys.argv[2]
    for url in sys.argv[3:]:
        m = SMART_Class[url]
        results = []
        print m.uri
        print key_to_mongo(sp.belongsTo)+".@iri"
        print record
        for result in  db[m.uri].find({key_to_mongo(sp.belongsTo)+".@iri": record}):
            results.append(result)
        tf = datetime.datetime.now() - ts
        print "Elapsed", tf
        v = RDFifier(results).graph.serialize()
        tf = datetime.datetime.now() - ts
        print "Elapsed", tf
    
if __name__ == "__main__":
    import sys, json
    from smart.models.record_object import RecordObject
    from pymongo import Connection
    import datetime

    c = Connection()
    db = c.records
    if sys.argv[1] == "write":
        for v in sys.argv[2:]:
            rid = filter(str.isdigit, v.split("/")[-1].split(".")[0])
            print "Adding data to patient", rid

            data = parse_rdf(open(v).read())

            var_bindings = {'record_id': rid}
            ro = RecordObject[sp.Statement]
            ro.prepare_graph(data, None, var_bindings)
            b = JSONifier(data)
            for k, v in b.statement_elements.iteritems():
                db[v['@type'][0]].insert(v)

    elif sys.argv[1] == "readone":
        import datetime
        url = sys.argv[2]
        print url
        m = SMART_Class["http://smartplatforms.org/terms#Medication"]
        print m.uri
        ts =  datetime.datetime.now()
        result = db[m.uri].find_one({'@subject.@iri': url})
        print RDFifier(result).graph.serialize()
        tf = datetime.datetime.now() - ts
        print "Elapsed", tf


    elif sys.argv[1] == "readall":
        readall()
        readall()
        readall()
