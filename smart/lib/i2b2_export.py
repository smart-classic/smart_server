from xml.dom import minidom
import libxml2, libxslt

from django.forms.fields import email_re
import django.core.mail as mail
import logging
import string, random
import functools

import psycopg2
import psycopg2.extras
import RDF
import httplib
import re
import os
from utils import *


ns = default_ns()
conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             ("i2b2demo",
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)


rxnconn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             ("rxnorm",
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))

rxncur = rxnconn.cursor(cursor_factory=psycopg2.extras.DictCursor)


def get_i2b2_patients():   
   q = """select distinct patient_num from patient_dimension order by patient_num;"""
   cur.execute(q)
   rows = cur.fetchall()
   
   patients = []
   for row in rows: patients.append(row['patient_num'])
   return patients   
   
def get_problems(p):
   q = """select concept_cd, 
       max(umls_cui) as umls_cui, 
       max(snomed_fsn) as snomed_fsn, 
       max(snomed_cid) as snomed_cid, 
       max(start_date) as start_date, 
       max(end_date) as end_date 
   from observation_fact f 
   join icd9_to_umls u on substr(f.concept_cd, 6, 10)=u.icd9 
   where patient_num=%s and concept_cd like 'ICD9%%' 
   group by concept_cd;"""
   cur.execute(q, (p,))
   rows = cur.fetchall()

   problems = []
   for row in rows: 
       p = i2problem()
       problems.append(p)
       p.title = row['snomed_fsn']
       p.umlsCui = row['umls_cui']
       p.snomedCID = row['snomed_cid']
       p.onset = row['start_date']
       p.resolution = row['end_date']
       p.external_id="%s"%len(problems)

   return problems


frequency_map = {"QD" : "daily", "QHS" : "at bed", "BID": "twice daily"}

def get_meds(p): 
    
   q = """select substr(concept_cd,5,20) as ndc,
       encounter_num,
        instance_num,
        modifier_cd,
       valtype_cd as valtype,
       tval_char as text_quantity,
       nval_num as quantity, 
       units_cd as units,
       start_date, end_date
       from observation_fact f 
       where patient_num=%s and concept_cd like 'NDC%%'
       order by encounter_num, concept_cd, modifier_cd;
       """
   cur.execute(q, (p,))
   rows = cur.fetchall()
   
   rxq = """ select str, rxcui from rxnconso where rxcui in 
   (SELECT rxcui FROM rxnsat WHERE  atn='NDC'  and atv=%s ) 
   and sab='RXNORM' and tty in ('SBD', 'SCD', 'BPCK', 'GPCK') limit 1;"""

   rxq_backup = """ select str, rxcui from rxnconso where rxcui in 
   (SELECT rxcui FROM rxnsat WHERE  atn='NDC'  and atv=%s ) 
    limit 1;"""

   rxq_details = """ select atn, atv from rxnsat 
   where rxcui=%s and sab='MMSL' 
   and atn in ('DDF', 'DRT', 'DST');"""

   meds = {}
   
   for r in rows:
        medkey = str(r['encounter_num'])+str(r['ndc'])+str(r['instance_num'])
        try:
           newmed = meds[medkey]
        except:
           assert str(r['modifier_cd']) == '@', "expecting one null modifer code per med"
           newmed = i2med()
           newmed.startDate = r['start_date']
           newmed.endDate = r['end_date']
           newmed.ndc = r['ndc']
           newmed.external_id="%s"%len(meds)
           newmed.dose = None
           newmed.doseUnit = None
           meds[medkey] = newmed
        
        if (r['modifier_cd'] == 'MED:DOSE'):            
            newmed.dose = str(r['quantity'])
            f = float(newmed.dose)
            if (f == int(f)): f = int(f)
            newmed.dose = str(f)
            newmed.doseUnit = r['units']

        if (r['modifier_cd'] == 'MED:FREQ'):
            newmed.frequency = frequency_map[r['text_quantity']]

   for newmed in meds.values():       
       try:       
           rxncur.execute(rxq, (newmed.ndc,))
           print "looking up " , newmed.ndc
           v = rxncur.fetchall()[0]
           newmed.rxcui=v['rxcui']
           newmed.title=v['str']
           
#           meds[-1].append([v['rxcui'],v['str']])
       except:
           print "resorting to backup query"
           rxncur.execute(rxq_backup, (newmed.ndc,))
           print "backup looking up " , newmed.ndc
           v = rxncur.fetchall()[0]
           newmed.rxcui=v['rxcui']
           newmed.title=v['str']
           print "and resolved to ", newmed.rxcui
       rxncur.execute(rxq_details, (newmed.rxcui,))
       v = rxncur.fetchall()
       attrs = {}
       newmed.strength = None
       newmed.strengthUnit = None
       newmed.route=None
       newmed.doseForm = None
       
       for vr in v:
           attrs[vr['atn']] = vr['atv']
       try:
           newmed.doseForm = attrs['DDF']
           newmed.route = attrs['DRT']
           strength = attrs['DST'].split(" ")
           if len(strength) == 1:
               newmed.strength = attrs['DST']
               newmed.strengthUnit = None
           else:
               newmed.strength = " ".join(filter(lambda x: re.match("^\d",x), strength[:-1]))
               newmed.strengthUnit = strength[-1]
       except: pass
           
   return meds.values()
    
def get_demographics(p):
   q = """select * from patient_dimension
       where patient_num=%s;"""
       
   cur.execute(q, (p,))
   rows = cur.fetchall()
   r = rows[0]
   
   d = i2demographic()
   d.givenName = 'Sample'
   d.familyName = str(p)
   d.birthday = r['birth_date']
   d.deathday = r['death_date']
   d.gender = r['sex_cd'] == "F" and "female" or "male"
   d.language = r['language_cd']
   d.race = r['race_cd']
   d.maritalStatus = r['marital_status_cd']
   d.religion  =r['religion_cd']
   d.zip = r['zip_cd']
   d.income = r['income_cd']
   
   return d
   
"""
from smart.lib.i2b2_export import *
"""

class  i2med(object):
    pass

class  i2problem(object):
    pass

class  i2demographic(object):
    pass


class i2b2Patient():
    def __init__(self, patient_id):
        self.id = patient_id
        self.get_problems()
        self.get_meds()
        self.get_demographics()
        
    def get_problems(self):
        self.problems = get_problems(self.id)
    def get_meds(self):
        self.meds = get_meds(self.id)
    def get_demographics(self):
        self.demographics = get_demographics(self.id)
    
    def rdf_med(self, med):
        m = RDF.Model()
        om = RDF.Node(blank="one_med")
        m.append(RDF.Statement(om, ns['rdf']['type'], ns['sp']['medication']))
        m.append(RDF.Statement(om, ns['dcterms']['title'], RDF.Node(literal=med.title.encode() )))
        m.append(RDF.Statement(om, ns['med']['drug'], ns['rxcui'][med.rxcui.encode()]))
        #m.append(RDF.Statement(om, ns['med']['ndc'], RDF.Node(literal=med.ndc.encode())))
        if med.dose:
            m.append(RDF.Statement(om, ns['med']['dose'], RDF.Node(literal=med.dose.encode())))
        if med.doseUnit:
            m.append(RDF.Statement(om, ns['med']['doseUnit'], RDF.Node(literal=med.doseUnit.encode())))
        if med.strength:
            m.append(RDF.Statement(om, ns['med']['strength'], RDF.Node(literal=med.strength.encode())))
        if (med.strengthUnit):
            m.append(RDF.Statement(om, ns['med']['strengthUnit'], RDF.Node(literal=med.strengthUnit.encode())))
        if (med.route):
            m.append(RDF.Statement(om, ns['med']['route'], RDF.Node(literal=med.route.encode())))
        if (med.frequency):
            m.append(RDF.Statement(om, ns['med']['frequency'], RDF.Node(literal=med.frequency.encode())))
        m.append(RDF.Statement(om, ns['med']['startDate'], RDF.Node(literal=med.startDate.isoformat()[:10].encode())))
        if (med.endDate):
            m.append(RDF.Statement(om, ns['med']['endDate'], RDF.Node(literal=med.endDate.isoformat()[:10].encode())))
        return m


    def rdf_problem(self, problem):
        m = RDF.Model()
        o = RDF.Node(blank="one_problem")
        m.append(RDF.Statement(o, ns['rdf']['type'], ns['sp']['problem']))
        m.append(RDF.Statement(o, ns['dcterms']['title'], RDF.Node(literal=problem.title.encode())))
        m.append(RDF.Statement(o, ns['umls']['cui'], RDF.Node(literal=problem.umlsCui.encode())))
        m.append(RDF.Statement(o, ns['umls']['snomed_cid'], RDF.Node(literal=problem.snomedCID.encode())))
        m.append(RDF.Statement(o, ns['sp']['onset'], RDF.Node(literal=problem.onset.isoformat()[:10].encode())))
        if (problem.resolution):    
                m.append(RDF.Statement(o, ns['sp']['resolution'], RDF.Node(literal=problem.resolution.isoformat()[:10].encode())))
        return m
    

            

    def rdf_demographics(self):
        d = self.demographics
        m = RDF.Model()
        o = RDF.Node(blank="one_demographic")
        m.append(RDF.Statement(o, ns['rdf']['type'], ns['foaf']['Person']))
        m.append(RDF.Statement(o, ns['foaf']['givenName'], RDF.Node(literal=d.givenName.encode())))
        m.append(RDF.Statement(o, ns['foaf']['familyName'], RDF.Node(literal=d.familyName.encode())))
        m.append(RDF.Statement(o, ns['foaf']['gender'], RDF.Node(literal=d.gender.encode())))
        if (d.zip):
            m.append(RDF.Statement(o, ns['spdemo']['zipcode'], RDF.Node(literal=d.zip.encode())))
        if (d.deathday):
            m.append(RDF.Statement(o, ns['spdemo']['deathday'], RDF.Node(literal=d.deathday.isoformat()[:10].encode())))
        if (d.birthday):
            m.append(RDF.Statement(o, ns['spdemo']['birthday'], RDF.Node(literal=d.birthday.isoformat()[:10].encode())))
        m.append(RDF.Statement(o, ns['spdemo']['language'], RDF.Node(literal=d.language.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['race'], RDF.Node(literal=d.race.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['maritalStatus'], RDF.Node(literal=d.maritalStatus.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['religion'], RDF.Node(literal=d.religion.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['income'], RDF.Node(literal=d.income.encode())))
        
        return m

    def write_to_files(self, base="."):
        
        base = os.path.join(base, "records")
        try:
            os.mkdir(base)
        except OSError: pass        
        
        base = os.path.join(base, "%s"%self.id)
        os.mkdir(base)
        os.mkdir(os.path.join(base, "medications"))
        os.mkdir(os.path.join(base, "problems"))
        os.mkdir(os.path.join(base, "demographics"))

        os.mkdir(os.path.join(base, "medications", "external_id"))
        os.mkdir(os.path.join(base, "problems", "external_id"))
        
        for m in self.meds:
            os.mkdir(os.path.join(base, "medications", "external_id",m.external_id))
            f = open(os.path.join(base, "medications/external_id/%s/data.rdf"%m.external_id), "w")
            f.write(serialize_rdf(self.rdf_med(m)))
            f.close()
            
        for p in self.problems:
            os.mkdir(os.path.join(base, "problems", "external_id", p.external_id))
            f = open(os.path.join(base, "problems/external_id/%s/data.rdf"%p.external_id), "w")
            f.write(serialize_rdf(self.rdf_problem(p)))
            f.close()
            
        f = open(os.path.join(base, "demographics/data.rdf"), "w")
        f.write(serialize_rdf(self.rdf_demographics()))
        f.close()
            
        
        
    @classmethod
    def initialize_all(cls):
        patient_ids = get_i2b2_patients()
        patients = []
        for p in patient_ids:
            patients.append(i2b2Patient(p))
            print "Writing patient ", len(patients), "to file"
            patients[-1].write_to_files()
            
        return patients
"""
from smart.lib.i2b2_export import *
ps = i2b2Patient.initialize_all()
for p in ps:
    
ps[0].write_to_files()
ps[0].rdf_demographics()
ps[0].rdf_problems()

"""