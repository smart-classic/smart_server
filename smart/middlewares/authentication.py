"""
Middleware (filters) for SMArt

inspired by django.contrib.auth middleware, but doing it differently
for tighter integration into email-centric users in SMART.
"""

from smart.accesscontrol import security
from smart.lib.utils import DjangoVersionDependentExecutor


class LazyUser(object):
    def __get__(self, request, obj_type = None):
        if not hasattr(request, '_cached_user'):
            request._cached_user = auth.get_user(request)
        return request._cached_user


class Authentication(object):

    def process_request(self, request):
        # django 1.3.0 fails to create a QueryDict for request.POST if we access
        # request.raw_post_data first, but django 1.3.1 raises an exception if
        # we read request.POST and subsequently read request.raw_post_data.
        #
        # So, we preemptively read the appropriate variable first, depending on
        # the current version of django
        self.avoid_post_clobbering(request)
        request.principal, request.oauth_request = security.get_principal(request)
    
    noclobber_map = {
        '1.3.0': lambda request: request.POST,
        '1.3.1+': lambda request: request.raw_post_data,
    }
    avoid_post_clobbering = DjangoVersionDependentExecutor(noclobber_map)

    def process_exception(self, request, exception):
        print "PROCESSING EXCEPTION"
        import sys, traceback
        print >> sys.stderr, exception, dir(exception)
        traceback.print_exc(file=sys.stderr)
        
        sys.stderr.flush()
