"""
Models for the Coding Systems
"""

from django.db import models
from django.conf import settings
from django.utils import simplejson
import RDF
import os, glob
import psycopg2
import psycopg2.extras


rdf = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
spl = RDF.NS("http://www.accessdata.fda.gov/spl/data/")
host = RDF.NS(settings.SITE_URL_PREFIX+"/spl/data/")

class JSONObject(object):
    JSON_FIELDS = []

    def toJSONDict(self):
        d = {}
        for f in self.JSON_FIELDS:
            d[f] = getattr(self, f)
        return d

    def toJSON(self):
        return simplejson.dumps(self.toJSONDict())
     

class SPL(JSONObject):
    def __init__(self, spl_set_id, spl_id=None):
        
        self.spl_set_id=spl_set_id.encode()
        self.dir = os.path.join(settings.APP_HOME, "structured_product_label/data/%s"%spl_set_id)

        if (spl_id == None):
            path = "%s/*.xml"%self.dir
            print "path", path
            print glob.glob(path)
            spl_id = os.path.split(glob.glob(path)[0])[1].split(".xml")[0]
                    
        self.xml = os.path.join(self.dir, spl_id)

        self.spl_id=spl_id.encode()
        self.node = RDF.Node(spl['%s/%s.xml'%(self.spl_id,self.spl_id)])
    
    def toRDF(self):
        self.model = RDF.Model()
        self.model.append(RDF.Statement(self.node, rdf["type"], spl['']))
        
        for image in glob.glob("%s/*.jpg"%self.dir):
            image = os.path.split(image)[1].encode()
            self.model.append(RDF.Statement(self.node, spl['image'], host['%s/%s'%(self.spl_set_id, image)]))
            
        s = RDF.RDFXMLSerializer()
        return s.serialize_model_to_string(self.model)
    


def SPL_from_rxn_concept(concept_id):
   rxcui_id = str(concept_id)

   conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             (settings.DATABASE_RXN, 
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))
   cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
   q = """SELECT upper(a1.atv) as SPL_SET_ID 
           FROM rxnsat a1 join rxnsat a2 on a1.rxaui=a2.rxaui 
           WHERE  a1.atn='SPL_SET_ID' 
                   and a1.rxcui=%s
                   and a2.atn='NDC' 
           GROUP BY a1.atv  
           ORDER BY count(*) DESC
           LIMIT 1;"""
  
   cur.execute(q, (rxcui_id,))
   rows = cur.fetchall()

   set_id = rows[0][0]
   return SPL(set_id)
        