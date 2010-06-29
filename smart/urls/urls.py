from django.conf.urls.defaults import *

from smart.views import *
from smart.lib.utils import MethodDispatcher

urlpatterns = patterns(
    '',
    # Homepage
    (r'^$', home),
    
    # OAuth
    (r'^oauth/', include('smart.urls.oauth')),
    
    (r'^version$', get_version),

    (r'^accounts/$', account_create),
    (r'^accounts/search$', account_search),
    (r'^accounts/(?P<account_email>[^/]+)$', account_info),
    (r'^accounts/(?P<account_email>[^/]+)/', include('smart.urls.account')),

    # Record
    (r'^records/(?P<record_id>[^/]+)$', record_info),
    (r'^records/(?P<record_id>[^/]+)/apps/$', record_apps),
    (r'^records/(?P<record_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': record_add_app,
                'DELETE': record_remove_app})),
    
    # PHAs
    (r'^apps/$', all_phas),
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),

    # SMArt API
    (r'^meds(?P<medcall>[^/]*)/records/(?P<record_id>[^/]+).*$', meds),
    (r'^rdf_store$', rdf_store),
    (r'^rdf_query$', rdf_query),
    (r'^rdf_dump$', rdf_dump),
    
    
    )
