import sys
import tempfile
import hotshot
import hotshot.stats
from django.conf import settings
from cStringIO import StringIO

class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def process_request(self, request):
        if settings.DEBUG:
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.prof = hotshot.Profile(self.tmpfile.name)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG:
            self.prof.close()

            stats = hotshot.stats.load(self.tmpfile.name)
            stats.sort_stats('time', 'calls')
            stats.print_stats()
        return response
