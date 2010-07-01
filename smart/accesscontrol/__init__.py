import sys
from smart import views

class PermissionSet(object):

  def __init__(self, principal):
    self.grants   = {}
    self.checkers = {}
    self.request  = {}
    self.principal    = principal
    self.view_args    = ()
    self.view_kwargs  = {}

  def grant(self, view_func, parameter_callbacks=None):
    self.grants[view_func] = parameter_callbacks

  def evaluate(self, request, view_func, view_args, view_kwargs):
    """
    a permission set is checked against a particular call.
    some information in the parameters here is duplicated, i.e. view_func depends on request,
    but it's provided here as convenience.
    """
    if not self.grants.has_key(view_func):
      return False

    callbacks = self.grants[view_func]

    # if callbacks is None, we're done, it's all good
    if callbacks == None:
      return True

    # otherwise, more constraints to check

    # the callbacks are checked, they must all be true to succeed
    # this is not as powerful as the Indivo full-fledged system, but
    # I'm waiting for that to be revamped before using it here in SMArt
    for callback in callbacks:
      if not callback(request, view_func, view_args, view_kwargs):
        return False

    return True


def get_accessrule(view_func):
  return None

def nouser_permset():
  permset = PermissionSet(None)
  grant_baseline(permset)
  return permset

def grant_baseline(permset):
  """Grant a common set of base grants"""
  
  # home
  permset.grant(views.home, None)

  # list the phas
  permset.grant(views.all_phas, None)

  # version
  permset.grant(views.get_version, None)
#
#  # SMArt API -- this should check perm based on app, user, record...
#  permset.grant(views.smarthacks.meds, [])
#  
  # static files
  # for development purposes
  import django.views.static
  permset.grant(django.views.static.serve, None)