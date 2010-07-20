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
    (r'^accounts/(?P<account_email>[^/]+)/recent_records/$', account_recent_records),
    (r'^accounts/(?P<account_email>[^/]+)/', include('smart.urls.account')),

    # Record
    (r'^record_by_token/$', record_by_token),
    (r'^records/search/$', record_search),
    (r'^records/(?P<record_id>[^/]+)$', record_info),
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': add_app,
                'DELETE': remove_app})),
                
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)/records/(?P<record_id>[^/]+)/launch$', launch_app),
    
    # PHAs
    (r'^apps/$', all_phas),
    (r'^apps/accounts/(?P<account_id>[^/]+)/$', apps_for_account),
    
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),

    # SMArt API
    (r'^rdf_store/$', MethodDispatcher({
                                       'GET': get_rdf_store,
                                       'PUT': put_rdf_store,
                                       'POST': post_rdf_store,
                                       'DELETE': delete_rdf_store,
                                       'OPTIONS' : allow_options})),

    (r'^med_store/records/(?P<record_id>[^/]*)/$', MethodDispatcher({
                                       'GET': get_rdf_meds,
                                       'PUT': put_rdf_meds,
                                       'POST': post_rdf_meds,
                                       'DELETE': delete_rdf_meds,
                                       'OPTIONS' : allow_options})))
