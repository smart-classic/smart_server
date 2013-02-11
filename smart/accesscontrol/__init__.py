import sys
import smart
#from smart import views


class PermissionSet(object):

    def __init__(self, principal):
        self.grants = {}
        self.checkers = {}
        self.request = {}
        self.principal = principal
        self.view_args = ()
        self.view_kwargs = {}

    def grant(self, view_func, parameter_callbacks=None):
        self.grants[view_func] = parameter_callbacks

    def evaluate(self, request, view_func, view_args, view_kwargs):
        """
        Returns a tuple: (success, message)

        A permission set is checked against a particular call.
        some information in the parameters here is duplicated, i.e. view_func
        depends on request, but it's provided here as convenience.
        """

        if view_func not in self.grants:
            return (False, 'You are not allowed to request %s' % request.META.get('PATH_INFO', view_func))

        callbacks = self.grants[view_func]

        # if callbacks is None, we're done, it's all good
        if callbacks is None:
            return (True, None)

        # otherwise, more constraints to check

        # the callbacks are checked, they must all be true to succeed
        # this is not as powerful as the Indivo full-fledged system, but
        # I'm waiting for that to be revamped before using it here in SMArt
        for callback in callbacks:
            if not callback(request, view_func, view_args, view_kwargs):
                return (False, None)        # TODO: Add error message

        return (True, None)


def get_accessrule(view_func):
    return None


def nouser_permset():
    permset = PermissionSet(None)
    grant_baseline(permset)
    return permset


def grant_baseline(permset):
    """Grant a common set of base grants"""

    # home
    permset.grant(smart.views.home, None)

    # list the phas
    permset.grant(smart.views.all_phas, None)

    # manifest
    permset.grant(smart.views.get_manifest, None)

    # static files for development purposes
    import django.views.static
    permset.grant(django.views.static.serve, None)

    # Anyone can make an OPTIONS request on a page
    permset.grant(smart.views.allow_options, None)
    permset.grant(smart.views.debug_oauth, None)
    permset.grant(smart.views.smarthacks.get_container_manifest, None)
    permset.grant(smart.views.smarthacks.download_ontology)
