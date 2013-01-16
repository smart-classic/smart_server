"""
Indivo Models

Ben Adida
Steve Zabak
"""

import urllib
import datetime

from django.db import models
from django.conf import settings

from base import Object, Principal, APP_LABEL

# SZ: We are no longer using for people


class Share(Object):
    """
    Sharing a record with a PHA
    """

    # the record that's being shared
    record = models.ForeignKey('Record', related_name='shares', null=True)
    with_app = models.ForeignKey(
        'OAuthApp', related_name='shares_to', null=True)

    # authorized
    authorized_at = models.DateTimeField(null=True, blank=True)

    # the user who added this share
    # there might not be one if this was primed, thus nullable
    authorized_by = models.ForeignKey(
        'Account', null=True, related_name='shares_authorized_by')

    # does this share enable offline access?
    # this only makes sense for PHA shares
    offline = models.BooleanField(default=False)

    class Meta:
        app_label = APP_LABEL
        unique_together = (('record', 'with_app', 'authorized_by'),)

    def new_access_token(self, token_str, token_secret):
        """
        create a new access token based on this share
        """
        expires_at = datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=60)

        return AccessToken.objects.create(
            token=token_str,
            token_secret=token_secret,
            share=self,
            expires_at=expires_at
        )


class Token(object):
    """
    Some common features of access and request tokens
    """

    def __str__(self):
        vars = {
            'oauth_token': self.token,
            'oauth_token_secret': self.token_secret
        }
        return urllib.urlencode(vars)

    @property
    def secret(self):
        return self.token_secret

    to_string = __str__


class AccessToken(Principal, Token):
    # the token, secret, and PHA this corresponds to
    token = models.CharField(max_length=40)
    token_secret = models.CharField(max_length=60)
    expires_at = models.DateTimeField(null=True)

    # derived from a share
    share = models.ForeignKey('Share')
    smart_connect_p = models.BooleanField(default=False)

    # make sure email is set
    def save(self, *args, **kwargs):
        self.email = "%s@accesstokens.smart-platforms.org" % self.token
        super(AccessToken, self).save(*args, **kwargs)

    @property
    def effective_principal(self):
        return self.share.with_app

    def __str__(self):
        vars = {
            'oauth_token': self.token,
            'oauth_token_secret': self.token_secret
        }
        if (self.share.record is not None):
            vars['record_id'] = self.share.record.id
        if (self.share.authorized_by is not None):
            vars['user_id'] = self.share.authorized_by.id

        return urllib.urlencode(vars)
    to_string = __str__

    @property
    def secret(self):
        return self.token_secret

    @property
    def passalong_params(self):
        c = {}
        c['smart_container_api_base'] = settings.SITE_URL_PREFIX
        c['smart_oauth_token'] = self.token
        c['smart_oauth_token_secret'] = self.secret
        c['smart_user_id'] = self.share.authorized_by.email
        c['smart_app_id'] = self.share.with_app.email

        if self.share.record:
            c['smart_record_id'] = self.share.record.id

        return c


class ReqToken(Principal, Token):
    token = models.CharField(max_length=40)
    token_secret = models.CharField(max_length=60)
    verifier = models.CharField(max_length=60)
    oauth_callback = models.CharField(max_length=500, null=True)

    app = models.ForeignKey('OAuthApp')

    record = models.ForeignKey('Record', null=True)

    # when authorized
    authorized_at = models.DateTimeField(null=True)

    # authorized by can be used to bind the request token first, before the
    # authorized_at is set.
    authorized_by = models.ForeignKey(
        'Account', null=True, related_name="authorized_reqtokens")

    # the share that this results in
    share = models.ForeignKey('Share', null=True)

    # make sure email is set
    def save(self, *args, **kwargs):
        self.email = "%s@requesttokens.smartplatforms.org" % self.token
        super(ReqToken, self).save(*args, **kwargs)

    @property
    def effective_principal(self):
        """
        a request token's identity is really the PHA it comes from.
        """
        return self.app

    @property
    def authorized(self):
        # only look for authorized_at, because sometimes
        # it's primed, and not authorized by a particular user
        return self.authorized_at is not None
