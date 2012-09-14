from xml.dom import minidom
from django.conf import settings
import django.core.mail as mail
import logging
import string, random
import functools

import psycopg2
import psycopg2.extras
import rdflib
import httplib
import re
import os
from smart.common.rdf_tools.util import *

loinc = Namespace("http://loinc.org/codes/")
rxcuins = Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXCUI/")
dcterms = Namespace("http://purl.org/dc/terms/")
snomedct = Namespace("http://www.ihtsdo.org/snomed-ct/concepts/")


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

def get_vitals(p):
   q = """select concept_cd, nval_num, units_cd, encounter_num, start_date,end_date from observation_fact where CONCEPT_CD in ('LOINC:8480-6', 'LOINC:8462-4', 'LOINC:8302-2') and patient_num=%s order by encounter_num;"""
   cur.execute(q, (p,))
   rows = cur.fetchall()
   encounters = {}
   for row in rows:
      en = encounters.setdefault(row['encounter_num'], {})

      c = row['concept_cd']
      v = row['nval_num']
      if c == 'LOINC:8480-6': # sbp
         en['sbp'] = v
      elif c == 'LOINC:8462-4':
         en['dbp'] = v
      elif c == 'LOINC:8302-2':
         en['height'] = v
      en['start_date'] = row['start_date'].isoformat()
      en['end_date'] = row['end_date'].isoformat()
      en['num'] = row['encounter_num']
#   print [(e.sbp, e.dbp, e.h, e.start_date, e.num) for e in encounters.values()]
   return encounters.values()

   
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

class  i2encounter(object):
    pass


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
        self.meds = []
        self.problems = []
        self.labs = []
        self.get_demographics()
        
#        self.get_problems()
#        self.get_meds()
#        self.get_labs()
        self.get_vitals()
        
    def get_problems(self):
        self.problems = get_problems(self.id)
    def get_meds(self):
        self.meds = get_meds(self.id)
    def get_vitals(self):
        self.vitals = get_vitals(self.id)

    def get_demographics(self):
        self.demographics = get_demographics(self.id)
    def get_labs(self):
        self.labs = get_labs(self.id)

    def rdf_vital(self, v):
       v = parse_rdf(vitals_template.substitute(**v))
       return v
    
    def rdf_med(self, med):
        m = bound_graph()
        om = BNode()
        m.add((om, rdf['type'], sp['Medication']))

        rxnormCode = BNode()
        m.add((rxnormCode, rdf['type'], sp['CodedValue']))
        m.add((rxnormCode, sp['code'], rxcuins[med.rxcui.encode()]))
        m.add((rxnormCode, dcterms['title'], Literal(med.title.encode())))
        m.add((om, sp['drugName'], rxnormCode))

        
        #m.add((om, sp['ndc'], Literal(med.ndc.encode())))
        if med.dose:
            m.add((om, sp['dose'], Literal(med.dose.encode())))
        if med.doseUnit:
            m.add((om, sp['doseUnit'], Literal(med.doseUnit.encode())))
        if med.strength:
            m.add((om, sp['strength'], Literal(med.strength.encode())))
        if (med.strengthUnit):
            m.add((om, sp['strengthUnit'], Literal(med.strengthUnit.encode())))
        if (med.route):
            m.add((om, sp['route'], Literal(med.route.encode())))
        if (med.frequency):
            m.add((om, sp['frequency'], Literal(med.frequency.encode())))
        m.add((om, sp['startDate'], Literal(med.startDate.isoformat()[:10].encode())))
        if (med.endDate):
            m.add((om, sp['endDate'], Literal(med.endDate.isoformat()[:10].encode())))
        return m


    def rdf_problem(self, problem):
        m = bound_graph()
        o = BNode()
        m.add((o, rdf['type'], sp['Problem']))
        
        snomedCode = BNode()
        m.add((snomedCode, rdf['type'], sp['CodedValue']))
        m.add((snomedCode, sp['code'], snomedct['concepts/'+problem.snomedCID.encode()]))
        m.add((snomedCode, dcterms['title'], Literal(problem.title.encode())))
        m.add((o, sp['problemName'], snomedCode))

        m.add((o, sp['onset'], Literal(problem.onset.isoformat()[:10].encode())))
        if (problem.resolution):    
                m.add((o, sp['resolution'], Literal(problem.resolution.isoformat()[:10].encode())))
        return m
    
    def rdf_lab(self, lab):
        m = bound_graph()
        o = BNode()
        
        m.add((o, rdf['type'], sp['LabResult']))
        
        loincCode = BNode()
        m.add((loincCode, rdf['type'], sp['CodedValue']))
        m.add((loincCode, sp['code'], loinc[lab.code]))
        m.add((loincCode, dcterms['title'], Literal(lab.title)))
        m.add((o, sp['labName'], loincCode))

        resulted = BNode()
        m.add((resulted, rdf['type'], sp['Attribution']))
        m.add((resulted, sp['startTime'], Literal(lab.startTime.isoformat())))
        m.add((o, sp['resulted'], resulted))

        res = BNode()
        if lab.type == 'quantitative':
            m.add((res, rdf['type'], sp['QuantitativeResult']))
            m.add((o, sp['quantitativeResult'], res))

            vau = BNode()
            m.add((vau, rdf['type'], sp['ValueAndUnit']))
            m.add((res, sp['valueAndUnit'], vau))
            m.add((vau,sp['value'], Literal(str(lab.nval).encode())))
            m.add((vau,sp['unit'], Literal(lab.unit)))

            if lab.normalRangeLower  and lab.normalRangeLower :
                nlRange = BNode()
                m.add((nlRange, rdf['type'], sp['ResultRange']))
                m.add((res,sp['normalRange'], nlRange))
                
                nlMin = BNode()
                m.add((nlMin, rdf['type'], sp['ValueAndUnit']))
                m.add((nlRange, sp['minimum'], nlMin))
                m.add((nlMin,sp['value'], Literal(lab.normalRangeLower)))
                m.add((nlMin,sp['unit'], Literal(lab.unit)))
                
                nlMax = BNode()
                m.add((nlMax, rdf['type'], sp['ValueAndUnit']))
                m.add((nlRange, sp['maximum'], nlMax))
                m.add((nlMax,sp['value'], Literal(lab.normalRangeUpper)))
                m.add((nlMax,sp['unit'], Literal(lab.unit)))
                
            
            

        else:
            m.add((res, rdf['type'], sp['QualitativeResult']))
            m.add((o, sp['qualitativeResult'], res))
            m.add((res, sp['value'], Literal(lab.tval.encode())))
            for v in lab.enumVals:
                m.add((res, sp['enumerationOption'], Literal(v.encode())))                
        
        return m
    

    def rdf_demographics(self):
        d = self.demographics
        m = bound_graph()
        o = BNode()
        m.add((o, rdf['type'], foaf['Person']))
        m.add((o, foaf['givenName'], Literal(d.givenName.encode())))
        m.add((o, foaf['familyName'], Literal(d.familyName.encode())))
        m.add((o, foaf['gender'], Literal(d.gender.encode())))
        if (d.zip):
            m.add((o, sp['zipcode'], Literal(d.zip.encode())))
        if (d.deathday):
            m.add((o, sp['deathday'], Literal(d.deathday.isoformat()[:10].encode())))
        if (d.birthday):
            m.add((o, sp['birthday'], Literal(d.birthday.isoformat()[:10].encode())))
        m.add((o, sp['language'], Literal(d.language.encode())))
        m.add((o, sp['race'], Literal(d.race.encode())))
        m.add((o, sp['maritalStatus'], Literal(d.maritalStatus.encode())))
        m.add((o, sp['religion'], Literal(d.religion.encode())))
        m.add((o, sp['income'], Literal(d.income.encode())))
        
        return m

    def add_all(self, model):
        for a in model:
            if a not in self.model:
                self.model.add(a)

    def write_to_files(self, base="."):
        
        base = os.path.join(base, "records")
        
        try:
            os.mkdir(base)
        except OSError: pass        
        
        f = open(os.path.join(base, "%s"%self.id), "w")

        self.model = bound_graph()
        
        for m in self.meds:
            self.add_all(self.rdf_med(m))
            
        for p in self.problems:
            self.add_all(self.rdf_problem(p))

        for l in self.labs:
            try:
                self.add_all(self.rdf_lab(l))
            except: pass

        for v in self.vitals:
            self.add_all(self.rdf_vital(v))


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

vitals_template = string.Template("""<rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:v="http://www.w3.org/2006/vcard/ns#" xmlns:foaf="http://xmlns.com/foaf/0.1/" xmlns:sp="http://smartplatforms.org/terms#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dcterms="http://purl.org/dc/terms/">
  <sp:VitalSigns>
    <dc:date>$start_date</dc:date>
    <sp:encounter>
      <sp:Encounter>
        <sp:startDate>$start_date</sp:startDate>
        <sp:endDate>$end_date</sp:endDate>
      </sp:Encounter>
    </sp:encounter>
    <sp:height>
      <sp:VitalSign>
       <sp:vitalName>
        <sp:CodedValue>
          <sp:code rdf:resource="http://loinc.org/codes/8302-2"/>
          <dcterms:title>Height (measured)</dcterms:title>
        </sp:CodedValue>
      </sp:vitalName>
      <sp:value>$height</sp:value>
      <sp:unit>m</sp:unit>
     </sp:VitalSign>
    </sp:height>
    <sp:bloodPressure>
      <sp:BloodPressure>
        <sp:systolic>
          <sp:VitalSign>
            <sp:vitalName>
              <sp:CodedValue>
                <sp:code rdf:resource="http://loinc.org/codes/8480-6"/>
                <dcterms:title>Systolic blood pressure</dcterms:title>
              </sp:CodedValue>
            </sp:vitalName>
            <sp:value>$sbp</sp:value>
            <sp:unit>mm[Hg]</sp:unit>
          </sp:VitalSign>
        </sp:systolic>
        <sp:diastolic>
          <sp:VitalSign>
            <sp:vitalName>
              <sp:CodedValue>
                <sp:code rdf:resource="http://loinc.org/codes/8462-4"/>
                <dcterms:title>Diastolic blood pressure</dcterms:title>
              </sp:CodedValue>
            </sp:vitalName>
            <sp:value>$dbp</sp:value>
            <sp:unit>mm[Hg]</sp:unit>
          </sp:VitalSign>
        </sp:diastolic>
      </sp:BloodPressure>
    </sp:bloodPressure>
  </sp:VitalSigns>
</rdf:RDF>""")
    
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
