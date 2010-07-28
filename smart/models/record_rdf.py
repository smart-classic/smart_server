"""
Record-wise RDF store (parent class) + medications, problems (child classes)

Josh Mandel
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from django.conf import settings
from smart.models.records import Record

class RecordRDF(Object):
  Meta = BaseMeta(True)
  record = models.ForeignKey(Record, unique=True)
  triples = models.XMLField(schema_path=
    "%s../schema/%s"%(settings.XSLT_STYLESHEET_LOC, "rdf.xsd"))

  def __unicode__(self):
    try:
        return 'Record RDF Store %s, for %s' % (self.id, self.principal)
    except:
        return 'Record RDF Store %s, for ?' % (self.id)


class Medication(RecordRDF):
  Meta = BaseMeta(False)
  def __unicode__(self):
    try:
        return 'Med Store %s, for %s' % (self.id, self.principal)
    except:
        return 'Med Store %s, for ?' % (self.id)

class Problem(RecordRDF):
  Meta = BaseMeta(False)
  def __unicode__(self):
    try:
        return 'Problem Store %s, for %s' % (self.id, self.principal)
    except:
        return 'Problem Store %s, for ?' % (self.id)
