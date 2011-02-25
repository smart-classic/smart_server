from smart.models.rdf_store import TemporaryStoreConnector, RecordStoreConnector
from smart.models.record_object import api_types, Record, RecordObject
from smart.common.util import parse_rdf, bound_graph
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
        self.data = parse_rdf(open(filename).read())
        self.target_model = bound_graph()
        
        with TemporaryStoreConnector() as  temp_connector:
            self.temp_connector = temp_connector
            self.target_id = target_id or temp_connector.temp_id

            # 1. For each known data type, extract relevant nodes
            for t in api_types:
                self.import_one_type(t)
                
            # 2. Load data into temp connector
            self.add_all(self.temp_connector, self.data)
            self.temp_connector.execute_transaction()
    
            # 3. Pull data out of temp connector by query
            #    (pares down results to legitimate triples)
            for t in api_types:
                self.extract_one_type(t)
    
            # 4. Copy extracted nodes to permanent RDF store
            self.write_to_record()
     
    def write_to_record(self):
            r, created = Record.objects.get_or_create(id=self.target_id)
            rconn = RecordStoreConnector(r)
            if not created:
                print "DESTROYING existing record"
                rconn.destroy_triples()
                
            self.add_all(rconn, self.target_model)
            rconn.execute_transaction()
        
    def import_one_type(self, t):
        if t.base_path == None: return

        ro = RecordObject[t.node]    
        var_bindings = {'record_id': self.target_id}
        r = ro.generate_uris(self.data, var_bindings)
    
    def extract_one_type(self, t):
        if t.base_path == None: return
        ro = RecordObject[t.node]
        matched = self.temp_connector.sparql(ro.query_all())
        parse_rdf(matched, model=self.target_model)

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
