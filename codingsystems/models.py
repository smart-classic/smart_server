"""
Models for the Coding Systems
"""

from django.db import models
from django.conf import settings
from django.utils import simplejson

class JSONObject(object):
    JSON_FIELDS = []

    def toJSONDict(self):
        d = {}
        for f in self.JSON_FIELDS:
            d[f] = getattr(self, f)
        return d

    def toJSON(self):
        return simplejson.dumps(self.toJSONDict())
                

class CodingSystem(models.Model):
    short_name = models.CharField(max_length = 100, unique=True)
    description = models.CharField(max_length = 2000, null = True)

    def search_codes(self, query_string, limit = 100):
        return [c for c in CodedValueVariant.objects.filter(coded_value__system = self, variant__icontains= query_string)[:limit]] +  [c for c in CodedValue.objects.filter(system = self,  full_value__icontains = query_string).order_by("full_value")[:limit]]

class CodedValue(models.Model, JSONObject):
    system = models.ForeignKey(CodingSystem)
    code = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=100, null=True)
    full_value = models.CharField(max_length=250)
    
    consumer_value = models.CharField(max_length=250, null=True)

    umls_code = models.CharField(max_length = 30, null = True)

    JSON_FIELDS = ['code', 'umls_code', 'abbreviation', 'full_value', 'consumer_value']

    class Meta:
        unique_together = (('system','code'))

class CodedValueVariant(models.Model, JSONObject):
    """
    a spelling/terminology variant of a coded value
    """

    JSON_FIELDS = ['code','umls_code', 'abbreviation', 'full_value', 'variant', 'consumer_value']

    coded_value = models.ForeignKey(CodedValue)
    variant = models.CharField(max_length=250)

    @property
    def code(self):
        return self.coded_value.code

    @property
    def umls_code(self):
        return self.coded_value.umls_code

    @property
    def abbreviation(self):
        return self.coded_value.abbreviation

    @property
    def full_value(self):
        return self.coded_value.full_value

    @property
    def consumer_value(self):
        return self.coded_value.consumer_value


import psycopg2
import psycopg2.extras

class CustomCodingSystem(object):
    @classmethod
    def get(cls, short_name):
        if short_name == "rxnorm_ingredient":
            return RxNormCodingSystem()
        elif short_name=="rxnorm_clinical_drug":
            return RxNormClinicalDrugCodingSystem()
        else: raise CodingSystem.DoesNotExist


class RxNormCode(JSONObject):
    def __init__(self, **kwargs):
        self.JSON_FIELDS = []
        for (k,v) in kwargs.iteritems():
            setattr(self, k, v)
            if k not in self.JSON_FIELDS:
                self.JSON_FIELDS.append(k)
    
    def set(self, k, v):
        setattr(self, k, v)


class RxNormCodingSystem(object):
    short_name = "rxnorm_ingredient"
    description = "RxNorm coding System"
    
    conn = psycopg2.connect("dbname='%s' user='%s' password='%s'" % 
                          (settings.DATABASE_RXN,
                           settings.DATABASE_USER,
                           settings.DATABASE_PASSWORD))

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def search_codes(self, query_string, limit = 100):
        q = """select rxcui, str, tty from rxnconso where str ilike %(q)s and sab='RXNORM' and tty in ('IN','BN');"""
        self.cur.execute(q, {'q': '%'+query_string+'%'})
        res =  self.cur.fetchall()

        ret = []        
        for r in res:
            ret.append(RxNormCode(code=r['rxcui'], tty=r['tty'], full_value=r['str']))
            
        return ret
    
    
class RxNormClinicalDrugCodingSystem(RxNormCodingSystem):
    short_name = "rxnorm_clinical_drug"
    atn_names = {'DDF': 'dose_form', 'DRT': 'dose_route', 'DST': 'dose_strength'}

    def search_codes(self, query_string, limit = 100):
        q = """select drug_rxcui, atn, max(atv) as atv from ingredients_to_drugs itd
            join rxnsat a on 
                a.rxcui=itd.drug_rxcui and
                a.sab='MMSL' and
                a.atn=ANY(array['DDF','DRT','DST'])
            where ingredient_rxcui=%s
            group by drug_rxcui, atn order by drug_rxcui, atn desc;"""
            
        self.cur.execute(q, (query_string,))
        res = self.cur.fetchall()
        
        codes = {}        
        for r in res:
            dc = r['drug_rxcui']
            if dc not in codes:
                codes[dc] = RxNormCode(code=dc, dose_form='', dose_route='', dose_strength='')
            codes[dc].set(self.atn_names[r['atn']], r['atv'])

        return sorted(codes.values(), key=lambda x: x.dose_route+x.dose_strength)