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

class PHA_RDFStore(Object):
  Meta = BaseMeta()
  PHA = models.ForeignKey(PHA, unique=True)
  triples = models.XMLField(schema_path=
    "%s../schema/%s"%(settings.XSLT_STYLESHEET_LOC, "rdf.xsd"))

  def __unicode__(self):
    try:
        return 'RDF Store %s, for %s' % (self.id, self.principal)
    except:
        return 'RDF Store %s, for ?' % (self.id)
