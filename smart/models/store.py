import datetime

from django.db import models
from django.conf import settings

from base import APP_LABEL, Object

class Store(Object):
    pha = models.ForeignKey('PHA', null=True)
    account = models.ForeignKey('Account', null=True)
    record = models.ForeignKey('Record', null=True)
    last_updated = models.DateTimeField(null=False, blank=False, auto_now=True, auto_now_add=True)
    data = models.TextField(null=True)
    mime = models.CharField(max_length=100, null=True)
  
class Meta:
    app_label = APP_LABEL
    unique_together = ('account', 'pha', 'record')