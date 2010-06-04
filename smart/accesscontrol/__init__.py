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

  def grant(self, view_func, parameter_callbacks):
    self.grants[view_func] = parameter_callbacks


## WORK HERE on SMART

def get_accessrule(view_func):
  pass

class PermissionSetAux:

  def _grant_baseline(self, permset):
    """Grant a common set of base grants"""

    # list the phas
    permset.grant(views.all_phas, None)

    # static files
    # for development purposes
    import django.views.static
    permset.grant(django.views.static.serve, None)
    return permset

  def get_permset(self, type_obj, grants=None, grant_baseline=True):
    """Get grants for a paricular principle"""

    permset = PermissionSet(type_obj)
    if grant_baseline:
      permset = self._grant_baseline(permset)
    return self.add_grants(permset, grants)

  def add_grants(self, permset, grants):
    """Add specific grants to the permset"""

    isiterable = lambda obj: isinstance(obj, basestring) or \
                              getattr(obj, '__iter__', False)

    if grants:
      for view, access_rule in grants.items():

        # access rules should always be of type list
        if not isinstance(access_rule, list):
          access_rule = [access_rule]

        if isiterable(access_rule):
          permset.grant(view, access_rule)
        else:
          return False
    return permset

  def transform_expr(self, expr):
    if not isinstance(expr, Operator):
      return expr
    expr[:] = map(self.transform_expr, expr)
    return expr


class Operator(list):
  """Generic Operator class"""

  def __init__(self, *args):
    super(Operator, self).__init__(args)

class Not(Operator):
  """Prop Cal Not"""

  def op(self, arg1):
    return not arg1

  def __str__(self):
    return '!(%s)' % tuple(self)

class And(Operator):
  """Prop Cal And"""

  def op(self, arg1, arg2):
    return arg1 and arg2

  def __str__(self):
    return '(%s & %s)' % tuple(self)

class Or(Operator):
  """Prop Cal Or"""

  def op(self, arg1, arg2):
    return arg1 or arg2

  def __str__(self):
    return '(%s | %s)' % tuple(self)
