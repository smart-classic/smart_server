"""
Records for SMArt bootstrap

Ben Adida
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *

class Record(Object):
  Meta = BaseMeta()

  full_name = models.CharField(max_length = 150, null= False)

  def __unicode__(self):
    return 'Record %s' % self.id

# Let's assume for now that all the accounts share a list of apps, e.g. the set chosen by a CIO or administrator.
#class AccountApp(Object):
#  record = models.ForeignKey(Record)
#  app = models.ForeignKey(PHA)
#
#  # uniqueness
#  class Meta:
#    app_label = APP_LABEL
#    unique_together = (('record', 'app'),)