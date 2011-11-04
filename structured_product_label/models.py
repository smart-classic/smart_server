"""
Models for the Coding Systems
"""

from django.db import models
from django.conf import settings
from django.utils import simplejson
import os, glob
import psycopg2
import psycopg2.extras
from smart.lib.utils import serialize_rdf
from xml.dom.minidom import parse, parseString
import libxml2
import urllib
from smart.client.common.util import *

pillbox_api_key = "7SETYPBTYS"
pillbox_url = "http://pillbox.nlm.nih.gov/PHP/pillboxAPIService.php"

spl = Namespace("http://www.accessdata.fda.gov/spl/data/")
pillbox = Namespace("http://pillbox.nlm.nih.gov/")
dcterms = Namespace('http://purl.org/dc/terms/')
host = Namespace(settings.SITE_URL_PREFIX+"/spl/data/")
rxnorm = Namespace("http://rxnav.nlm.nih.gov/REST/rxcui/")




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
    spl_type = URIRef("http://www.accessdata.fda.gov/spl/data")
    def __init__(self, spl_set_id, spl_id=None):
        
        self.spl_set_id=spl_set_id.encode()
        self.dir = os.path.join(settings.APP_HOME, "structured_product_label/data/%s"%spl_set_id)

        if (spl_id == None):
            path = "%s/*.xml"%self.dir
            spl_id = os.path.split(glob.glob(path)[0])[1].split(".xml")[0]
                    
        self.xml = os.path.join(self.dir, "%s.xml"%spl_id)
        
        
        self.spl_id=spl_id.encode()
        self.node = URIRef(spl['%s/%s.xml'%(self.spl_id,self.spl_id)])
        self.model = bound_graph()
        self.model.add((self.node, rdf["type"], SPL.spl_type))
        
        f = open(self.xml)
        d = libxml2.parseDoc(f.read())    
        f.close()
        c = d.xpathNewContext()
        c.xpathRegisterNs("spl", "urn:hl7-org:v3")
        org_name = c.xpathEval("//spl:representedOrganization//spl:name")[0].content
        org_name = URIRef(org_name)
        self.model.add((self.node, spl["representedOrganization"], org_name))

        ndcs =  [x.content for  x in c.xpathEval("//spl:code[@codeSystem='2.16.840.1.113883.6.69']/@code")]
        for ndc in ndcs:
            if len(ndc.split("-")) != 2: continue # dont' need to distinguish 20- vs. 40-pill bottles...
            ndc = URIRef(ndc)
            self.model.add((self.node, spl["NDC"], ndc))
            
   
        for image in glob.glob("%s/*.jpg"%self.dir):
            image = os.path.split(image)[1].encode()
            self.model.add((self.node, spl['image'], host['%s/%s'%(self.spl_set_id, image)]))

class IngredientPillBox(JSONObject):
    def __init__(self, rxcui_id):
        self.rxcui_id = rxcui_id
        self.model = bound_graph()

        try:
            self.ingredient = self.getIngredient()
            self.getPillboxData()
        except:
            return
        
        for pill in self.data.getElementsByTagName("pill"):
           has_image = pill.getElementsByTagName("HAS_IMAGE")[0].childNodes[0].nodeValue
           if (has_image == "1"):
               self.addPill(pill)



    def addPill(self, pill):
        product_code =   pill.getElementsByTagName("PRODUCT_CODE")[0].childNodes[0].nodeValue.encode()
        image_id = pill.getElementsByTagName("image_id")[0].childNodes[0].nodeValue.encode()
        label = pill.getElementsByTagName("RXSTRING")[0].childNodes[0].nodeValue.encode()
        
        this_pill_node = URIRef("%s?prodcode=%s"%(pillbox_url, product_code))
        
        self.model.add((
                                      rxnorm[self.rxcui_id], 
                                      pillbox["pill"], 
                                      this_pill_node))
        
        self.model.add((this_pill_node, rdf["type"], pillbox["pill"]))
        self.model.add((this_pill_node, spl["NDC"], URIRef(product_code)))

        self.model.add((this_pill_node, 
                                pillbox['image'], 
                                URIRef('http://pillbox.nlm.nih.gov/assets/medium/%smd.jpg'%(image_id))))

        self.model.add((this_pill_node, 
                                dcterms["title"], 
                                URIRef(label)))
        


    def getIngredient(self):
       conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                                 (settings.DATABASE_RXN, 
                                  settings.DATABASE_USER, 
                                  settings.DATABASE_PASSWORD))
       cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
       
       q = """select distinct(lower(split_part(str, ' ' ,1))) 
                   from rxnconso where rxcui=%s LIMIT 1;"""
       
       cur.execute(q, (self.rxcui_id,))
       rows = cur.fetchall()
       name = rows[0][0]
       return name

                    
    def getPillboxData(self):
       print "FETCHING", "%s?has_image=1&key=%s&ingredient=%s"%(pillbox_url, pillbox_api_key, self.ingredient)
       pillbox_xml = urllib.urlopen("%s?has_image=1&key=%s&ingredient=%s"%(pillbox_url, pillbox_api_key, self.ingredient)).read()
       
       d = parseString(pillbox_xml)
       self.data = d
       return
   
    

def merge_models(models):
    m = bound_graph()
    for one_model in models:
        if hasattr(one_model, "model"):
            m += one_model.model
        else: m += one_model
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

   ret = [IngredientPillBox(rxcui_id)]
   
   for row in rows:
       set_id = row[0]
       
       try:
           one_spl = SPL(set_id)
       except:
           continue
       
       ret.append(one_spl)
              
       one_spl.model.add((
                                      rxnorm[concept_id], 
                                      SPL.spl_type, 
                                      one_spl.node))
    
   return ret
