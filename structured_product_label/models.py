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
from smart.lib.utils import serialize_rdf
from xml.dom.minidom import parse, parseString
import urllib

pillbox_api_key = "7SETYPBTYS"
pillbox_url = "http://pillbox.nlm.nih.gov/PHP/pillboxAPIService.php"
rdf = RDF.NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
spl = RDF.NS("http://www.accessdata.fda.gov/spl/data/")
spl_type = RDF.Node(uri_string="http://www.accessdata.fda.gov/spl/data")
pillbox = RDF.NS("http://pillbox.nlm.nih.gov/")
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
        self.model = RDF.Model()
        self.model.append(RDF.Statement(self.node, rdf["type"], spl_type))
        for image in glob.glob("%s/*.jpg"%self.dir):
            image = os.path.split(image)[1].encode()
            self.model.append(RDF.Statement(self.node, spl['image'], host['%s/%s'%(self.spl_set_id, image)]))
    
    def getPillboxImages(self, rxcui_id):
       conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                                 (settings.DATABASE_RXN, 
                                  settings.DATABASE_USER, 
                                  settings.DATABASE_PASSWORD))
       cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
       
       q = """select distinct(lower(split_part(str, ' ' ,1))) 
                   from rxnconso where rxcui=%s and sab='MTHSPL' LIMIT 1;"""
       
       cur.execute(q, (rxcui_id,))
       rows = cur.fetchall()
       name = rows[0][0]
       pillbox_xml = urllib.urlopen("%s?has_image=1&key=%s&ingredient=%s"%(pillbox_url, pillbox_api_key, name)).read()
       try:
           d = parseString(pillbox_xml)
       except:
            return

       for image_node in d.getElementsByTagName("image_id"):
           image_id = image_node.childNodes[0].nodeValue.encode()

           self.model.append(RDF.Statement(self.node, 
                                            pillbox['image'], 
                                        RDF.Node(uri_string='http://pillbox.nlm.nih.gov/assets/medium/%smd.jpg'%(image_id))))
       return

    
    def toRDF(self):
        return serialize_rdf(self.model)
    


def merge_models(spls):
    m = RDF.Model()
    for spl in spls:
        for s in spl.model:
            m.append(s)
    return serialize_rdf(m)

def SPL_from_rxn_concept(concept_id):
   concept_id=concept_id.encode()
   rxcui_id = str(concept_id)

   conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             (settings.DATABASE_RXN, 
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))
   cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
   q = """SELECT distinct(upper(a1.atv)) as SPL_SET_ID
           FROM rxnsat a1 
           WHERE  a1.atn='SPL_SET_ID' 
                   and a1.rxcui=%s;"""

   cur.execute(q, (rxcui_id,))
   rows = cur.fetchall()

   ret = []
   for row in rows:
       set_id = row[0]
       one_spl = SPL(set_id)
       
       one_spl.model.append(RDF.Statement(
                                      RDF.Node(uri_string="http://link.informatics.stonybrook.edu/rxnorm/RXCUI/%s"%concept_id), 
                                      spl_type, 
                                      one_spl.node))

       
       ret.append(one_spl)
    
   if (len(ret) > 0):
        ret[0].getPillboxImages(rxcui_id)
    
       
   return ret