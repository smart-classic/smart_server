"""
Indivo Models

Ben Adida
Steve Zabak
"""

import urllib

from django.db import models
from django.conf import settings

from base import Object, Principal, APP_LABEL

# SZ: We are no longer using for people
class Share(Object):
  """
  Sharing an account with a PHA
  """

  # the account that's being shared
  account = models.ForeignKey('Account', related_name = 'shares')
  with_pha = models.ForeignKey('PHA', related_name='shares_to', null=True)

  # authorized
  authorized_at = models.DateTimeField(null=True, blank=True)

  # the user who added this share
  # there might not be one if this was primed, thus nullable
  authorized_by = models.ForeignKey('Account', null=True, related_name = 'shares_authorized_by')

  # does this share enable offline access?
  # this only makes sense for PHA shares
  offline = models.BooleanField(default = False)

  class Meta:
    app_label = APP_LABEL
    unique_together = (('account', 'with_pha'),)
    

  def new_access_token(self, token_str, token_secret):
    """
    create a new access token based on this share

    if an account is specified, it's a short-term session access token.
    if not, it's a long-term token

    """
    return AccessToken.objects.create(token=token_str, token_secret=token_secret, share=self)

class Token(object):
  """
  Some common features of access and request tokens
  """

  def __str__(self):
    vars = {'oauth_token' : self.token, 'oauth_token_secret' : self.token_secret}
    return urllib.urlencode(vars)

  @property
  def secret(self):
    return self.token_secret

  to_string = __str__
  

class AccessToken(Principal, Token):
  # the token, secret, and PHA this corresponds to
  token = models.CharField(max_length=40)
  token_secret = models.CharField(max_length=60)

  # derived from a share
  share = models.ForeignKey('Share')

  # make sure email is set 
  def save(self, *args, **kwargs):
    self.email = "%s@accesstokens.smart-platforms.org" % self.token
    super(AccessToken,self).save(*args, **kwargs)
  
  @property
  def effective_principal(self):
      return self.share.with_pha



class ReqToken(Principal, Token):
  token = models.CharField(max_length=40)
  token_secret = models.CharField(max_length=60)
  verifier = models.CharField(max_length=60)
  oauth_callback = models.CharField(max_length=500, null=True)

  pha = models.ForeignKey('PHA')

  # account or carenet
  account = models.ForeignKey('Account', null=True)

  # when authorized
  authorized_at = models.DateTimeField(null=True)

  # authorized by can be used to bind the request token first, before the authorized_at is set.
  authorized_by = models.ForeignKey('Account', null = True, related_name="authorized_reqtokens")

  # the share that this results in
  share = models.ForeignKey('Share', null=True)

  # make sure email is set 
  def save(self, *args, **kwargs):
    self.email = "%s@requesttokens.indivo.org" % self.token
    super(ReqToken,self).save(*args, **kwargs)
  
  @property
  def effective_principal(self):
    """
    a request token's identity is really the PHA it comes from.
    """
    return self.pha

  @property
  def authorized(self):
    # only look for authorized_at, because sometimes 
    # it's primed, and not authorized by a particular user
    return self.authorized_at != None