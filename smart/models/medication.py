"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from django.conf import settings
from smart.models.records import Record

class Medication(Object):
  Meta = BaseMeta()
  record = models.ForeignKey(Record, unique=True)
  triples = models.XMLField(schema_path=
    "%s../schema/%s"%(settings.XSLT_STYLESHEET_LOC, "rdf.xsd"))

  def __unicode__(self):
    try:
        return 'Med Store %s, for %s' % (self.id, self.principal)
    except:
        return 'Med Store %s, for ?' % (self.id)
