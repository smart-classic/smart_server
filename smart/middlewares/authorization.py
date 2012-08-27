"""
Middleware (filters) for SMArt (inspired by Indivo)

inspired by django.contrib.auth middleware, but doing it differently
for tighter integration into email-centric users in Indivo.
"""

import re
import smart

from time import strftime
from django.http import *
from django.core.exceptions import PermissionDenied
from django.conf import settings

from smart import accesscontrol


class Authorization(object):
    """Authorization class to authorize incoming calls
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """ The process_view() hook allows us to examine the request before
        view_func is called
        """

        # Bypass authorization check for some calls
        for exc_pattern in settings.SMART_ACCESS_CONTROL_EXCEPTIONS:
            if re.match(exc_pattern, request.path):
                return None

        if hasattr(view_func, 'resolve'):
            view_func = view_func.resolve(request)

        denied_message = None
        try:
            if view_func:
                permission_set = self.get_permset(request)

                # given a set of permissions, and a rule for access checking
                # apply the rules to the permission set with the current request
                # parameters
#                import rpdb2
#                rpdb2.start_embedded_debugger("a")
                if permission_set:
                    success, message = permission_set.evaluate(request, view_func, view_args, view_kwargs)
                    if success:
                        print "And permitted for %s %s" % (view_func.__name__, request.principal)
                        return None
                    denied_message = message
                    print "Permission denied for %s %s: %s" % (view_func.__name__, request.principal, message)

        # otherwise, this will fail
        except:
            print "Exception: Permission denied for %s %s" % (view_func.__name__, request.principal)
            import sys
            import traceback
            traceback.print_exc(file=sys.stderr)
            raise PermissionDenied

        # TODO: Can we return something that actually shows the message? Stupid Django :P
        raise PermissionDenied

    def get_permset(self, request):
        if request.principal:
            "The permset is for", request.principal
            return request.principal.permset
        else:
            "The permset is for nouser"
            return smart.accesscontrol.nouser_permset()


# Mark that the authorization module has been loaded
# nothing gets served otherwise
smart.AUTHORIZATION_MODULE_LOADED = True
