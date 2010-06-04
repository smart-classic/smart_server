from django.conf.urls.defaults import *

from smart.views import *
from smart.lib.utils import MethodDispatcher

urlpatterns = patterns(
    '',
    # Homepage
    #(r'^$', home),
    
    # OAuth
    (r'^oauth/', include('smart.urls.oauth')),
    
    (r'^version$', get_version),
    # Current identity
    (r'^id$', get_id),

    # PHAs
    (r'^apps/$', all_phas),
    
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
    
    )
