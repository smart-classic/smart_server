from xml.dom import minidom
import libxml2, libxslt
from django.conf import settings
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
from smart.common.util import *

loinc = RDF.NS("http://loinc.org/codes/")
rxcuins = RDF.NS("http://link.informatics.stonybrook.edu/rxnorm/RXCUI/")
dcterms = RDF.NS("http://purl.org/dc/terms/")
snomedct = RDF.NS("http://www.ihtsdo.org/snomed-ct/concepts/")


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


def get_i2b2_patients(offset=0):   
   q = """select distinct patient_num from patient_dimension order by patient_num offset %s;"""%offset
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

def get_labs(p):
   q = """select f.encounter_num, f.start_date, 
   f.valtype_cd, f.tval_char, f.nval_num, f.units_cd,
   f.concept_cd, cd.name_char, i.c_metadataxml
   from observation_fact f 
   join concept_dimension cd on cd.concept_cd=f.concept_cd 
   join i2b2 i on i.c_fullname=cd.concept_path
where f.concept_cd like 'LOINC:%%' and
patient_num=%s and cd.concept_path like '%%LOINC%%';"""
   cur.execute(q, (p,))
   rows = cur.fetchall()
   
   def xval(d, vname):
       try:
          return  d.getElementsByTagName(vname)[0].childNodes[0].data.encode()
       except: 
          return None
   def xvals(d, vname):
       return  [x.childNodes[0].data.encode() for x in d.getElementsByTagName(vname)]

   labs = []
   for row in rows: 
       l = i2lab()
       labs.append(l)
       l.external_id="%s"%len(labs)
       
       l.type = row['valtype_cd'] == 'N' and "quantitative" or "qualitative"
       l.tval = row['tval_char'].encode()
       l.nval = row['nval_num']
       l.unit = row['units_cd'].encode()
       l.code = row['concept_cd'].split("LOINC:",1)[1].encode()
       l.title= row['name_char'].encode().split(" (LOINC",1)[0]
       l.startTime = row['start_date']
       
       try:
           d = minidom.parseString(row['c_metadataxml'])
           l.dataType = xval(d, "DataType")
           l.normalUnit = xval(d, "NormalUnits")
           l.normalRangeLower = xval(d, "HighofLowValue")
           l.normalRangeUpper = xval(d, "LowofHighValue")
           l.nonCriticalRangeLower = xval(d, "LowofLowValue")
           l.nonCriticalRangeLower = xval(d, "HighofHighValue")
           l.enumVals = xvals(d, "Val")
           l.row = row
           if l.unit == "@" and l.type=="quantitative" and l.normalUnit:
               l.unit = l.normalUnit
               print "bum units now", l.unit

       except: pass #print "couldn't parse for", len(labs), row

   
       
   return labs



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

class  i2lab(object):
    pass


class i2b2Patient():
    def __init__(self, patient_id):
        self.id = patient_id
        self.get_problems()
        self.get_meds()
        self.get_demographics()
        self.get_labs()
        
    def get_problems(self):
        self.problems = get_problems(self.id)
    def get_meds(self):
        self.meds = get_meds(self.id)
    def get_demographics(self):
        self.demographics = get_demographics(self.id)
    def get_labs(self):
        self.labs = get_labs(self.id)
    
    def rdf_med(self, med):
        m = RDF.Model()
        om = RDF.Node()
        m.append(RDF.Statement(om, rdf['type'], sp['Medication']))

        rxnormCode = RDF.Node()
        m.append(RDF.Statement(rxnormCode, rdf['type'], sp['CodedValue']))
        m.append(RDF.Statement(rxnormCode, sp['code'], rxcuins[med.rxcui.encode()]))
        m.append(RDF.Statement(rxnormCode, dcterms['title'], RDF.Node(literal=med.title.encode())))
        m.append(RDF.Statement(om, sp['drugName'], rxnormCode))

        
        #m.append(RDF.Statement(om, sp['ndc'], RDF.Node(literal=med.ndc.encode())))
        if med.dose:
            m.append(RDF.Statement(om, sp['dose'], RDF.Node(literal=med.dose.encode())))
        if med.doseUnit:
            m.append(RDF.Statement(om, sp['doseUnit'], RDF.Node(literal=med.doseUnit.encode())))
        if med.strength:
            m.append(RDF.Statement(om, sp['strength'], RDF.Node(literal=med.strength.encode())))
        if (med.strengthUnit):
            m.append(RDF.Statement(om, sp['strengthUnit'], RDF.Node(literal=med.strengthUnit.encode())))
        if (med.route):
            m.append(RDF.Statement(om, sp['route'], RDF.Node(literal=med.route.encode())))
        if (med.frequency):
            m.append(RDF.Statement(om, sp['frequency'], RDF.Node(literal=med.frequency.encode())))
        m.append(RDF.Statement(om, sp['startDate'], RDF.Node(literal=med.startDate.isoformat()[:10].encode())))
        if (med.endDate):
            m.append(RDF.Statement(om, sp['endDate'], RDF.Node(literal=med.endDate.isoformat()[:10].encode())))
        return m


    def rdf_problem(self, problem):
        m = RDF.Model()
        o = RDF.Node()
        m.append(RDF.Statement(o, rdf['type'], sp['Problem']))
        
        snomedCode = RDF.Node()
        m.append(RDF.Statement(snomedCode, rdf['type'], sp['CodedValue']))
        m.append(RDF.Statement(snomedCode, sp['code'], snomedct['concepts/'+problem.snomedCID.encode()]))
        m.append(RDF.Statement(snomedCode, dcterms['title'], RDF.Node(literal=problem.title.encode())))
        m.append(RDF.Statement(o, sp['problemName'], snomedCode))

        m.append(RDF.Statement(o, sp['onset'], RDF.Node(literal=problem.onset.isoformat()[:10].encode())))
        if (problem.resolution):    
                m.append(RDF.Statement(o, sp['resolution'], RDF.Node(literal=problem.resolution.isoformat()[:10].encode())))
        return m
    
    def rdf_lab(self, lab):
        m = RDF.Model()
        o = RDF.Node()
        
        m.append(RDF.Statement(o, rdf['type'], sp['LabResult']))
        
        loincCode = RDF.Node()
        m.append(RDF.Statement(loincCode, rdf['type'], sp['CodedValue']))
        m.append(RDF.Statement(loincCode, sp['code'], loinc[lab.code]))
        m.append(RDF.Statement(loincCode, dcterms['title'], RDF.Node(literal=lab.title)))
        m.append(RDF.Statement(o, sp['labName'], loincCode))

        resulted = RDF.Node()
        m.append(RDF.Statement(resulted, rdf['type'], sp['Attribution']))
        m.append(RDF.Statement(resulted, sp['startTime'], RDF.Node(literal=lab.startTime.isoformat())))
        m.append(RDF.Statement(o, sp['resulted'], resulted))

        res = RDF.Node()
        if lab.type == 'quantitative':
            m.append(RDF.Statement(res, rdf['type'], sp['QuantitativeResult']))
            m.append(RDF.Statement(o, sp['quantitativeResult'], res))

            vau = RDF.Node()
            m.append(RDF.Statement(vau, rdf['type'], sp['ValueAndUnit']))
            m.append(RDF.Statement(res, sp['valueAndUnit'], vau))
            m.append(RDF.Statement(vau,sp['value'], RDF.Node(literal=str(lab.nval).encode())))
            m.append(RDF.Statement(vau,sp['unit'], RDF.Node(literal=lab.unit)))

            if lab.normalRangeLower  and lab.normalRangeLower :
                nlRange = RDF.Node()
                m.append(RDF.Statement(nlRange, rdf['type'], sp['ResultRange']))
                m.append(RDF.Statement(res,sp['normalRange'], nlRange))
                
                nlMin = RDF.Node()
                m.append(RDF.Statement(nlMin, rdf['type'], sp['ValueAndUnit']))
                m.append(RDF.Statement(nlRange, sp['minimum'], nlMin))
                m.append(RDF.Statement(nlMin,sp['value'], RDF.Node(literal=lab.normalRangeLower)))
                m.append(RDF.Statement(nlMin,sp['unit'], RDF.Node(literal=lab.unit)))
                
                nlMax = RDF.Node()
                m.append(RDF.Statement(nlMax, rdf['type'], sp['ValueAndUnit']))
                m.append(RDF.Statement(nlRange, sp['maximum'], nlMax))
                m.append(RDF.Statement(nlMax,sp['value'], RDF.Node(literal=lab.normalRangeUpper)))
                m.append(RDF.Statement(nlMax,sp['unit'], RDF.Node(literal=lab.unit)))
                
            
            

        else:
            m.append(RDF.Statement(res, rdf['type'], sp['QualitativeResult']))
            m.append(RDF.Statement(o, sp['qualitativeResult'], res))
            m.append(RDF.Statement(res, sp['value'], RDF.Node(literal=lab.tval.encode())))
            for v in lab.enumVals:
                m.append(RDF.Statement(res, sp['enumerationOption'], RDF.Node(literal=v.encode())))                
        
        return m
    

    def rdf_demographics(self):
        d = self.demographics
        m = RDF.Model()
        o = RDF.Node()
        m.append(RDF.Statement(o, rdf['type'], foaf['Person']))
        m.append(RDF.Statement(o, foaf['givenName'], RDF.Node(literal=d.givenName.encode())))
        m.append(RDF.Statement(o, foaf['familyName'], RDF.Node(literal=d.familyName.encode())))
        m.append(RDF.Statement(o, foaf['gender'], RDF.Node(literal=d.gender.encode())))
        if (d.zip):
            m.append(RDF.Statement(o, sp['zipcode'], RDF.Node(literal=d.zip.encode())))
        if (d.deathday):
            m.append(RDF.Statement(o, sp['deathday'], RDF.Node(literal=d.deathday.isoformat()[:10].encode())))
        if (d.birthday):
            m.append(RDF.Statement(o, sp['birthday'], RDF.Node(literal=d.birthday.isoformat()[:10].encode())))
        m.append(RDF.Statement(o, sp['language'], RDF.Node(literal=d.language.encode())))
        m.append(RDF.Statement(o, sp['race'], RDF.Node(literal=d.race.encode())))
        m.append(RDF.Statement(o, sp['maritalStatus'], RDF.Node(literal=d.maritalStatus.encode())))
        m.append(RDF.Statement(o, sp['religion'], RDF.Node(literal=d.religion.encode())))
        m.append(RDF.Statement(o, sp['income'], RDF.Node(literal=d.income.encode())))
        
        return m

    def add_all(self, model):
        for a in model.find_statements(RDF.Statement(None,None,None)):
            if a not in self.model:
                self.model.add_statement(a)

    def write_to_files(self, base="."):
        
        base = os.path.join(base, "records")
        
        try:
            os.mkdir(base)
        except OSError: pass        
        
        f = open(os.path.join(base, "%s"%self.id), "w")

        self.model = RDF.Model()
        
        for m in self.meds:
            self.add_all(self.rdf_med(m))
            
        for p in self.problems:
            self.add_all(self.rdf_problem(p))

        for l in self.labs:
            try:
                self.add_all(self.rdf_lab(l))
            except: pass

        self.add_all(self.rdf_demographics())

        f.write(serialize_rdf(self.model))
        f.close()
            
        
        
    @classmethod
    def initialize_all(cls, offset=0):
        patient_ids = get_i2b2_patients(offset)
        patients = []
        for p in patient_ids:
            patients.append(i2b2Patient(p))
            print "Writing patient ", len(patients), "to file"
            patients[-1].write_to_files()
            
        return patients
    
if __name__ == "__main__":
    ps = i2b2Patient.initialize_all()
    for p in ps:            
        p.write_to_files()
        
"""
from smart.lib.i2b2_export import *
ps = i2b2Patient.initialize_all()
for p in ps:
    
ps[0].write_to_files()
ps[0].rdf_demographics()
ps[0].rdf_problems()

"""