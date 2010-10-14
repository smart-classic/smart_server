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
       p.onset = row['start_date']
       p.resolution = row['end_date']
   return problems

def get_meds(p): 
    
   q = """select substr(concept_cd,5,20) as ndc, 
       nval_num as quantity, 
       units_cd as units,
       start_date, end_date
       from observation_fact f 
       where patient_num=%s and concept_cd like 'NDC%%';
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


   meds = []
   
   for r in rows:
       newmed = i2med()
       meds.append(newmed)
       
       try:       
           rxncur.execute(rxq, (r['ndc'],))
           print "looking up " , r['ndc']
           v = rxncur.fetchall()[0]
           newmed.rxcui=v['rxcui']
           newmed.title=v['str']
           
#           meds[-1].append([v['rxcui'],v['str']])
       except:
           print "resorting to backup query"
           rxncur.execute(rxq_backup, (r['ndc'],))
           print "backup looking up " , r['ndc']
           v = rxncur.fetchall()[0]
           print "and backed up by ", meds[-1]
           newmed.rxcui=v['rxcui']
           newmed.title=v['str']
           
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
       
       newmed.dose = str(r['quantity'])
       if (newmed.dose == "None"): newmed.dose = ""
       try:
         f = float(newmed.dose)
         newmed.dose = str(f)
       except: pass
       
       newmed.doseUnit = r['units'].lower()
       if (newmed.doseUnit == "@"): newmed.doseUnit = ""
       
       newmed.startDate = r['start_date']
       newmed.endDate = r['end_date']
       newmed.ndc = r['ndc']
   return meds
    
def get_demographics(p):
   q = """select * from patient_dimension
       where patient_num=%s;"""
       
   cur.execute(q, (p,))
   rows = cur.fetchall()
   r = rows[0]
   
   d = i2demographic()
   d.givenName = 'AnonPatient'
   d.familyName = str(p)
   d.birthday = r['birth_date']
   d.deathday = r['death_date']
   d.gender = r['sex_cd'] == "F" and "female" or "male"
   d.language = r['language_cd']
   d.race = r['race_cd']
   d.maritalStatus = r['marital_status_cd']
   d.religion  =r['religion_cd']
   d.zip = r['zip_cd']
   
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
    
    def rdf_meds(self):
        ret = []
        for med in self.meds:
            m = RDF.Model()
            om = RDF.Node(blank="one_med")
            m.append(RDF.Statement(om, ns['rdf']['type'], ns['sp']['medication']))
            m.append(RDF.Statement(om, ns['dcterms']['title'], RDF.Node(literal=med.title.encode() )))
            m.append(RDF.Statement(om, ns['med']['drug'], ns['rxcui'][med.rxcui.encode()]))
            m.append(RDF.Statement(om, ns['med']['ndc'], RDF.Node(literal=med.ndc.encode())))
            if med.dose:
                m.append(RDF.Statement(om, ns['med']['dose'], RDF.Node(literal=med.dose.encode())))
                m.append(RDF.Statement(om, ns['med']['doseUnit'], RDF.Node(literal=med.doseUnit.encode())))
            if med.strength:
                m.append(RDF.Statement(om, ns['med']['strength'], RDF.Node(literal=med.strength.encode())))
            if (med.strengthUnit):
                m.append(RDF.Statement(om, ns['med']['strengthUnit'], RDF.Node(literal=med.strengthUnit.encode())))
            if (med.route):
                m.append(RDF.Statement(om, ns['med']['route'], RDF.Node(literal=med.route.encode())))
            m.append(RDF.Statement(om, ns['med']['startDate'], RDF.Node(literal=med.startDate.isoformat()[:10].encode())))
            m.append(RDF.Statement(om, ns['med']['endDate'], RDF.Node(literal=med.endDate.isoformat()[:10].encode())))
            ret.append(m)
        return ret


    def rdf_problems(self):
        ret = []
        for problem in self.problems:
            m = RDF.Model()
            o = RDF.Node(blank="one_problem")
            m.append(RDF.Statement(o, ns['rdf']['type'], ns['sp']['problem']))
            m.append(RDF.Statement(o, ns['dcterms']['title'], RDF.Node(literal=problem.title.encode())))
            m.append(RDF.Statement(o, ns['umls']['cui'], RDF.Node(literal=problem.umlsCui.encode())))
            m.append(RDF.Statement(o, ns['sp']['onset'], RDF.Node(literal=problem.onset.isoformat()[:10].encode())))
            m.append(RDF.Statement(o, ns['sp']['resolution'], RDF.Node(literal=problem.resolution.isoformat()[:10].encode())))
            ret.append(m)
        return ret

            

    def rdf_demographics(self):
        d = self.demographics
        m = RDF.Model()
        o = RDF.Node(blank="one_demographic")
        m.append(RDF.Statement(o, ns['rdf']['type'], ns['foaf']['Person']))
        m.append(RDF.Statement(o, ns['foaf']['givenName'], RDF.Node(literal=d.givenName.encode())))
        m.append(RDF.Statement(o, ns['foaf']['familyName'], RDF.Node(literal=d.familyName.encode())))
        m.append(RDF.Statement(o, ns['foaf']['gender'], RDF.Node(literal=d.gender.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['birthday'], RDF.Node(literal=d.birthday.isoformat()[:10].encode())))
        if (d.zip):
            m.append(RDF.Statement(o, ns['spdemo']['zipcode'], RDF.Node(literal=d.zip.encode())))
        if (d.deathday):
            m.append(RDF.Statement(o, ns['spdemo']['deathday'], RDF.Node(literal=d.deathday.isoformat()[:10].encode())))
        m.append(RDF.Statement(o, ns['spdemo']['language'], RDF.Node(literal=d.language.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['race'], RDF.Node(literal=d.race.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['maritalStatus'], RDF.Node(literal=d.maritalStatus.encode())))
        m.append(RDF.Statement(o, ns['spdemo']['religion'], RDF.Node(literal=d.religion.encode())))
        
        return [m]

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
        
        i = 0
        for m in self.rdf_meds():
            i  += 1
            f = open(os.path.join(base, "medications/%03.d"%i), "w")
            f.write(serialize_rdf(m))
            f.close()
            
        i = 0
        for m in self.rdf_problems():
            i  += 1
            f = open(os.path.join(base, "problems/%03.d"%i), "w")
            f.write(serialize_rdf(m))
            f.close()
            
        i = 0
        for m in self.rdf_demographics():
            i  += 1
            f = open(os.path.join(base, "demographics/%03.d"%i), "w")
            f.write(serialize_rdf(m))
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