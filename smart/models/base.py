"""
SMArt

Indivo Models

Ben Adida
"""

from django.db import models
from django.conf import settings

import hashlib
import uuid

import string
import logging

from datetime import datetime, timedelta
from oauth import oauth

# generate the right meta class
APP_LABEL = 'smart'

def BaseMeta(abstract_p=False):
  class Meta:
    app_label = APP_LABEL
    abstract = abstract_p
  return Meta

class BaseModel(models.Model):
  """
  The base for all indivo models
  """
  Meta = BaseMeta(True)

  @classmethod
  def setup(cls):
    """
    called automatically after this class has been prepared into the server
    """
    pass

# SZ: Why is this called Object?
class Object(BaseModel):

  id = models.CharField(max_length = 50, primary_key = True)
  created_at = models.DateTimeField(auto_now_add = True)
  modified_at = models.DateTimeField(auto_now_add = True, auto_now = True)
  creator = models.ForeignKey('Principal', related_name = '%(class)s_created_by', null = True)

  def __unicode__(self):
    return "Core Object %s" % self.id

  Meta = BaseMeta(True)

  def save(self, **kwargs):
    if not self.id:
      self.id = str(uuid.uuid4())
    super(Object, self).save(**kwargs)


class Principal(Object):
  Meta = BaseMeta()

  # every principal is associated with an email address
  email = models.CharField(max_length = 300, unique = True)

  # effectively the descendent table
  type = models.CharField(max_length = 100)

  def save(self, *args, **kwargs):
    """
    make sure some fields are set
    """
    if not self.type or self.type == '':
      self.type = self.__class__.__name__
    super(Principal,self).save(*args, **kwargs)

  def grant_permissions(self, permset):
    """
    grant the permissions that this principal has to this permset.
    """
    from smart import accesscontrol
    from smart.accesscontrol import rules

    accesscontrol.grant_baseline(permset)
    rules.grant_by_principal(self, permset)

  @property
  def permset(self):
    from smart import accesscontrol
    permset = accesscontrol.PermissionSet(self)
    self.grant_permissions(permset)
    return permset
  
  @property
  def effective_principal(self):
    """
    In some cases, a principal's effective principal is not quite itself,
    e.g. a token's identity is really the PHA it comes from.
    """
    return self

  @property
  def proxied_by(self):
    """
    Principals are sometimes proxied by other principals, e.g. a PHA
    By default, principals are not proxied.
    """
    return None

  @property
  def effective_email(self):
    return self.effective_principal

  def __unicode__(self):
    return 'Principal %s' % self.email

  def __eq__(self, other):
    if not other or not isinstance(other, Principal):
      return False

    return self.id == other.id

