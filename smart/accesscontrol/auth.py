"""
Authentication for Indivo

Ben Adida - ben.adida@childrens.harvard.edu
"""

from django.http import HttpResponse, HttpResponseRedirect, Http404
import logging
import functools
import urllib
from django.core.exceptions import PermissionDenied
from smart import models

USER_ID = "_user_id"
NUM_LOGIN_ATTEMPTS = '_num_login_attempts'


def authenticate(request, username, password=None, system=None):
    """Check credentials

    """
    try:
        if password:
            user = models.AccountAuthSystem.objects.get(
                auth_system=models.AuthSystem.PASSWORD(),
                username=urllib.unquote(username)
            ).account
            if user.is_active and user.password_check(password):
                user.on_successful_login()
                return user

            user.on_failed_login()
            raise PermissionDenied()

        elif system:
            user = models.AccountAuthSystem.objects.get(
                auth_system=models.AuthSystem.objects.get(short_name=system),
                username=urllib.unquote(username)
            ).account
            if user.is_active:
                return user

            raise PermissionDenied()
    except:
        raise PermissionDenied()
    return False
