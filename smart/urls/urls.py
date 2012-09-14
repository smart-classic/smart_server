from django.conf.urls.defaults import include, patterns
from smart.views import *
from smart.models.ontology_url_patterns import OntologyURLMapper
from smart.models.record_object import RecordObject

urlpatterns = patterns('')

"""
Remaining API calls are dealt with individually, below.
"""     
urlpatterns += patterns(
    '',
    # Homepage
    (r'^$', home),
    
    # OAuth
    (r'^oauth/debug', debug_oauth),
    (r'^oauth/', include('smart.urls.oauth')),

    # Record
    (r'^record_by_token/$', record_by_token),
    (r'^records/search/xml$', record_search_xml),
    (r'^records/search$', record_search),
    (r'^records/(?P<record_id>[^/]+)$', record_info),

    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': add_app,
                'DELETE': remove_app})),
                
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<pha_email>[^/]+)/launch', launch_app),
    
    (r'^users/$', MethodDispatcher({ 'POST': user_create,'OPTIONS' : allow_options})),
    (r'^users/reset_password_request$', MethodDispatcher({'POST': user_reset_password_request})),
    (r'^users/reset_password$', MethodDispatcher({'POST': user_reset_password})),

    
    # PHAs
    (r'^apps/$', all_phas),
    (r'^apps/accounts/(?P<account_id>[^/]+)/$', apps_for_account),
    (r'^activity/(?P<activity_name>[^/]+)/app/(?P<app_id>[^/]+)$', resolve_activity_with_app),
    (r'^activity/(?P<activity_name>[^/]+)$', resolve_activity),
    (r'^apps/manifests/?$', all_manifests),
    (r'^apps/(?P<descriptor>.+)/manifest$', MethodDispatcher({
                                       'GET': resolve_manifest,
                                       'PUT': manifest_put,
                                       'DELETE': manifest_delete,
                                       'OPTIONS' : allow_options})),
    
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),

    # SMArt API                                       
    (r'^users/(?P<user_id>[^/]+)/apps/(?P<pha_email>[^/]+)/preferences', MethodDispatcher({
                                       'GET': preferences_get,
                                       'PUT': preferences_put,
                                       'DELETE': preferences_delete,
                                       'OPTIONS' : allow_options})),

    (r'^webhook/(?P<webhook_name>[^/]+)$', MethodDispatcher({
                                       'GET': do_webhook,
                                       'POST': do_webhook,
                                       'OPTIONS' : allow_options})),  

    (r'^apps/(?P<app_email>[^/]+)/tokens/records/first$', get_first_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)/next$', get_next_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)$', get_record_tokens),

    (r'^accounts/(?P<account_email>[^/]+)/alerts/(?P<alert_id>[^/]+)/acknowledge', account_acknowledge_alert),    
    (r'^records/(?P<record_id>[^/]+)/alerts/all', record_get_alerts),    

    (r'^accounts/search$', account_search),
    (r'^accounts/(?P<account_email>[^/]+)$', account_info),
    (r'^accounts/(?P<account_email>[^/]+)/recent_records/$', account_recent_records),
    (r'^accounts/(?P<account_email>[^/]+)/', include('smart.urls.account')),    

    (r'^records/create/proxied', MethodDispatcher({ 'POST': create_proxied_record})),
    (r'^records/(?P<record_id>[^/]+)/generate_direct_url', MethodDispatcher({ 'GET': generate_direct_url })),
    (r'^session/from_direct_url', MethodDispatcher({ 'GET': session_from_direct_url }))
  )

"""
Record objects (meds, fills, notes, problems, etc.) are handled (when possible)
in an ontology-driven way:  rdfobjects loads the ontology, registers
handlers for all the relevant paths (e.g. /records/{record_id}/medications/)
and specified methods (GET, POST, PUT, DELETE).
"""
from smart.plugins import *

OntologyURLMapper(urlpatterns) 
