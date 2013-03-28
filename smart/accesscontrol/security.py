"""
A number of security utilities for Indivo (used in SMArt)

based on django constructs
and Indivo data models

Ben Adida (ben.adida@childrens.harvard.edu)
2008-12-29
"""

from django.core.exceptions import *

import functools
import copy
import logging

from oauth import oauth, djangoutils

from smart import models
from smart.accesscontrol.oauth_servers import ADMIN_OAUTH_SERVER, OAUTH_SERVER, SMART_CONNECT_OAUTH_SERVER, SESSION_OAUTH_SERVER, HELPER_APP_SERVER


##
## Gather information about the request
##
def get_oauth_info(request, server):
    try:
        oauth_request = server.extract_oauth_request(djangoutils.extract_request(request))
        consumer, token, parameters = server.check_resource_access(oauth_request)
        return consumer, token, parameters, oauth_request
    except oauth.OAuthError as e:
        return None, None, None, None


def get_principal(request):
    """Figure out the principal making the request.

    First SMArt connect app (via web user); then web user; then PHA; then
    Helper app; then Chrome App sudo'ing.
    """

    # Look for a SMArt Connect Request, which comes signed with an empty
    # "consumer secret"
    pha, token, parameters, oauth_request = get_oauth_info(request, SMART_CONNECT_OAUTH_SERVER)
    if pha and token:
        return token, oauth_request

    # is this a chrome app with a user session token?
    chrome_app, token, parameters, oauth_request = get_oauth_info(request, SESSION_OAUTH_SERVER)
    if token:
        return token.user, oauth_request

    # check oauth
    # IMPORTANT: the principal is the token, not the PHA itself
    # TODO: is this really the right thing, is the token the principal?
    pha, token, parameters, oauth_request = get_oauth_info(request, OAUTH_SERVER)
    if pha:
        if token:
            return token, oauth_request
        return pha, oauth_request

    ha, token, parameters, oauth_request = get_oauth_info(request, HELPER_APP_SERVER)
    if ha:
        if token:
            return token, oauth_request
        return ha, oauth_request

        # check a machine application
    admin_app, token, params, oauth_request = get_oauth_info(request, ADMIN_OAUTH_SERVER)

    if admin_app:
        return admin_app, oauth_request

    return None, None
