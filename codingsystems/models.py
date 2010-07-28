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
        return [c for c in CodedValueVariant.objects.filter(coded_value__system = self, variant__icontains= query_string)[:limit]] + [c for c in CodedValue.objects.filter(system = self, full_value__icontains = query_string)[:limit]]

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
