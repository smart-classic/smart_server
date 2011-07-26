from smart.models.rdf_store import TemporaryStoreConnector, RecordStoreConnector
from smart.models.record_object import api_types, Record, RecordObject
from smart.common.util import parse_rdf, serialize_rdf, remap_node, bound_graph, URIRef, BNode, sp
from django.conf import settings
import sys

"""
To run:

PYTHONPATH=/path/to/smart_server \
  DJANGO_SETTINGS_MODULE=settings \
  /usr/bin/python \
  load_tools/load_one_patient.py \
  records/* 
"""
class RecordImporter(object):
    def __init__(self, filename, target_id=None):            
        # 0. Read supplied data
        self.target_id = target_id
        self.data = parse_rdf(open(filename).read())

        # 1. For each known data type, extract relevant nodes
        var_bindings = {'record_id': self.target_id}
        ro = RecordObject[sp.MedicalDataElement]    
        ro.prepare_graph(self.data, None, var_bindings)
            
        # 2. Copy extracted nodes to permanent RDF store
        self.write_to_record()
     
    def write_to_record(self):
            r, created = Record.objects.get_or_create(id=self.target_id)
            rconn = RecordStoreConnector(r)
            if not created:
                print "DESTROYING existing record"
                rconn.destroy_triples()
                
            self.add_all(rconn, self.data)
            print "adds: ",len(rconn.pending_adds)
            rconn.execute_transaction()
        
    @staticmethod
    def add_all(connector, model):
        for a in model:
            connector.pending_adds.append(a)

if __name__ == "__main__":
    import string
    for v in sys.argv[1:]:
        rid = filter(str.isdigit, v.split("/")[-1].split(".")[0])
        print "Using record id: %s"%rid
        RecordImporter(v, rid)
