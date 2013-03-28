"""
OAuth servers for users and admins

Ben Adida
ben.adida@childrens.harvard.edu
"""

import oauth.oauth as oauth

from django.db import transaction
from django.conf import settings
from smart import models

import datetime
import logging


class UserDataStore(oauth.OAuthStore):
    """
    Layer between Python OAuth and Django database
    for user applications (PHAs)
    """

    def _get_app(self, consumer_key):
        try:
            return models.PHA.objects.get(consumer_key=consumer_key)
        except models.PHA.DoesNotExist:
            return None

    def _get_token(self, token_str, app=None):
        kwargs = {'token': token_str}
        if app:
            kwargs['share__with_app'] = app

        try:
            ret = models.AccessToken.objects.get(**kwargs)
            if ret.smart_connect_p:
                oauth.report_error(
                    "Got a SMArt Connect Request -- should be a REST request"
                )
            return ret
        except models.AccessToken.DoesNotExist:
            return None

    def verify_request_token_verifier(self, request_token, verifier):
        """
        Verify whether a request token's verifier matches
        The verifier is stored right in the request token itself
        """
        return request_token.verifier == verifier

    def lookup_consumer(self, consumer_key):
        """
        looks up a consumer
        """
        return self._get_app(consumer_key)

    def create_request_token(self, consumer,
                             request_token_str,
                             request_token_secret,
                             verifier,
                             oauth_callback,
                             record_id=None,
                             offline_capable=False):
        """
        take a RequestToken and store it.

        anything after request_token_secret is extra kwargs custom to this
        server.
        """

        # look for the record that this might be mapped to
        # IMPORTANT: if the user who authorizes this token is not authorized
        # to admin the record, it will be a no-go
        record = None
        if record_id:
            try:
                record = models.Record.objects.get(id=record_id)
            except models.Record.DoesNotExist:
                pass

        # (BA) added record to the req token now that it can store it
        # (BA 2010-05-06) added offline_capable
        return models.ReqToken.objects.create(
            app=consumer,
            token=request_token_str,
            token_secret=request_token_secret,
            verifier=verifier,
            oauth_callback=oauth_callback,
            record=record
        )
#                                         offline = offline_capable)

    def lookup_request_token(self, consumer, request_token_str):
        """
        token is the token string
        returns a OAuthRequestToken

        consumer may be null.
        """
        try:
            # (BA) fix for consumer being null when we don't know yet who the consumer is
            if consumer:
                return models.ReqToken.objects.get(token=request_token_str, app=consumer)
            else:
                return models.ReqToken.objects.get(token=request_token_str)
        except models.ReqToken.DoesNotExist:
            return None

    def authorize_request_token(self, request_token, record=None, account=None, offline=False):
        """
        Mark a request token as authorized by the given user,
        with the given additional parameters.

        This means the sharing has beeen authorized, so the Share should be added now.
        This way, if the access token process fails, a re-auth will go through automatically.

        The account is whatever data structure was received by the OAuthServer.
        """

        request_token.authorized_at = datetime.datetime.utcnow()
        request_token.authorized_by = account

        # store the share in the request token
        # added use of defaults to reduce code size if creating an object
        share, create_p = models.Share.objects.get_or_create(
            record=record,
            with_app=request_token.app,
            authorized_by=account,
            defaults={
                'offline': offline,
                'authorized_at': request_token.authorized_at
            }
        )

        request_token.share = share
        request_token.save()

    def mark_request_token_used(self, consumer, request_token):
        """
        Mark that this request token has been used.
        Should fail if it is already used
        """
        new_rt = models.ReqToken.objects.get(
            app=consumer, token=request_token.token)

        # authorized?
        if not new_rt.authorized:
            raise oauth.OAuthError("Request Token not Authorized")

        new_rt.delete()

    def create_access_token(self, consumer, request_token, access_token_str, access_token_secret):
        """
        Store the newly created access token that is the exchanged version of this
        request token.

        IMPORTANT: does not need to check that the request token is still
        valid, as the library will ensure that this method is never called
        twice on the same request token, as long as mark_request_token_used
        appropriately throws an error the second time it's called.
        """

        share = request_token.share

        # create an access token for this share
        t = share.new_access_token(access_token_str, access_token_secret)
        return t

    def lookup_access_token(self, consumer, access_token_str):
        """
        token is the token string
        returns a OAuthAccessToken
        """
        return self._get_token(token_str=access_token_str, app=consumer)

    def check_and_store_nonce(self, nonce_str):
        """
        store the given nonce in some form to check for later duplicates

        IMPORTANT: raises an exception if the nonce has already been stored
        """
        nonce, created = models.Nonce.objects.get_or_create(nonce=nonce_str)
        if not created:
            raise oauth.OAuthError("Nonce already exists")


class HelperAppDataStore(UserDataStore):
    def __init__(self, *args, **kwargs):
        super(HelperAppDataStore, self).__init__(*args, **kwargs)

    def _get_app(self, consumer_key):
        #print "In helper app data store", consumer_key
        try:
            ret = models.HelperApp.objects.get(consumer_key=consumer_key)
            return ret
        except models.HelperApp.DoesNotExist:
            return None

    def _get_token(self, token_str, app=None):
        kwargs = {'token': token_str}
        if app:
            kwargs['share__with_app'] = app
        try:
            return models.AccessToken.objects.get(**kwargs)
        except models.AccessToken.DoesNotExist:
            return None


class MachineDataStore(oauth.OAuthStore):
    """
    Layer between Python OAuth and Django database.
    """

    def __init__(self, type=None):
        self.type = type

    def _get_machine_app(self, consumer_key):
        try:
            if self.type:
                return models.MachineApp.objects.get(app_type=self.type, consumer_key=consumer_key)
            else:
                # no type, we look at all machine apps
                return models.MachineApp.objects.get(consumer_key=consumer_key)
        except models.MachineApp.DoesNotExist:
            return None

    def lookup_consumer(self, consumer_key):
        return self._get_machine_app(consumer_key)

    def lookup_request_token(self, consumer, request_token_str):
        return None

    def lookup_access_token(self, consumer, access_token_str):
        return None

    def check_and_store_nonce(self, nonce_str):
        """
        store the given nonce in some form to check for later duplicates

        IMPORTANT: raises an exception if the nonce has already been stored
        """
        nonce, created = models.Nonce.objects.get_or_create(nonce=nonce_str)
        if not created:
            raise oauth.OAuthError("Nonce already exists")


class SessionDataStore(oauth.OAuthStore):
    """
    Layer between Python OAuth and Django database.

    An oauth-server for in-RAM chrome-app user-specific tokens
    """

    def _get_chrome_app(self, consumer_key):
        try:
            ret = models.MachineApp.objects.get(
                consumer_key=consumer_key, app_type='chrome')
            return ret
        except models.MachineApp.DoesNotExist:
            return None

    def _get_request_token(self, token_str, type=None, pha=None):
        try:
            ret = models.SessionRequestToken.objects.get(token=token_str)
            return ret
        except models.SessionRequestToken.DoesNotExist:
            return None

    def _get_token(self, token_str, type=None, pha=None):
        try:
            ret = models.SessionToken.objects.get(token=token_str)
            return ret
        except models.SessionToken.DoesNotExist:
            return None

    def lookup_consumer(self, consumer_key):
        """
        looks up a consumer
        """
        return self._get_chrome_app(consumer_key)

    def create_request_token(self, consumer, request_token_str, request_token_secret, verifier, oauth_callback):
        """
        take a RequestToken and store it.

        the only parameter is the user that this token is mapped to.
        """

        # we reuse sessiontoken for request and access
        token = models.SessionRequestToken.objects.create(
            token=request_token_str, secret=request_token_secret)
        return token

    def lookup_request_token(self, consumer, request_token_str):
        """
        token is the token string
        returns a OAuthRequestToken

        consumer may be null.
        """
        return self._get_request_token(token_str=request_token_str)

    def authorize_request_token(self, request_token, user=None):
        """
        Mark a request token as authorized by the given user,
        with the given additional parameters.

        The user is whatever data structure was received by the OAuthServer.
        """
        request_token.user = user
        request_token.authorized_p = True
        request_token.save()

    def mark_request_token_used(self, consumer, request_token):
        """
        Mark that this request token has been used.
        Should fail if it is already used
        """
        if not request_token.authorized_p:
            raise oauth.OAuthError("request token not authorized")

        request_token.delete()

    def create_access_token(self, consumer, request_token, access_token_str, access_token_secret):
        """
        Store the newly created access token that is the exchanged version of
        this request token.

        IMPORTANT: does not need to check that the request token is still
        valid, as the library will ensure that this method is never called
        twice on the same request token, as long as mark_request_token_used
        appropriately throws an error the second time it's called.
        """

        token = models.SessionToken.objects.create(token=access_token_str,
                                                   secret=access_token_secret,
                                                   user=request_token.user)
        return token

    def lookup_access_token(self, consumer, access_token_str):
        """
        token is the token string
        returns a OAuthAccessToken
        """
        return self._get_token(access_token_str)

    def check_and_store_nonce(self, nonce_str):
        """
        store the given nonce in some form to check for later duplicates

        IMPORTANT: raises an exception if the nonce has already been stored
        """
        pass


class SMArtConnectDataStore(SessionDataStore):
    """
    Hybrid datastore that looks for
        * a chrome app consumer
        * a smart connect access token.
    """

    def _get_chrome_app(self, consumer_key):
        try:
            return models.MachineApp.objects.get(consumer_key=consumer_key, app_type='chrome')
        except models.MachineApp.DoesNotExist:
            return None

    def _get_token(self, token_str, app=None):
        kwargs = {'token': token_str}
        #print "evaluating as SC, looking for", token_str
        try:

            ret = models.AccessToken.objects.get(**kwargs)
            if not ret.smart_connect_p:
                oauth.report_error(
                    "Not a SMArt Connect Request -- don't treat as one!")
            return ret
        except models.AccessToken.DoesNotExist:
            oauth.report_error(
                "No token means this isn't a SMArt Connect Request!")

ADMIN_OAUTH_SERVER = oauth.OAuthServer(store=MachineDataStore())
SESSION_OAUTH_SERVER = oauth.OAuthServer(store=SessionDataStore())
OAUTH_SERVER = oauth.OAuthServer(store=UserDataStore())
SMART_CONNECT_OAUTH_SERVER = oauth.OAuthServer(store=SMArtConnectDataStore())
HELPER_APP_SERVER = oauth.OAuthServer(store=HelperAppDataStore())
