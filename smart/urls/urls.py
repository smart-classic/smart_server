from django.conf.urls.defaults import include, patterns
from smart.views import *

urlpatterns = patterns('')
"""
Record objects (meds, fills, notes, problems, etc.) are handled (when possible)
in an ontology-driven way:  rdfobjects loads the ontology, registers
handlers for all the relevant paths (e.g. /records/{record_id}/medications/)
and specified methods (GET, POST, PUT, DELETE).
"""

for p in api_calls:
    urlpatterns += patterns( '',
                             (p.django_path(),  
                              MethodDispatcher(p.getMethods()), 
                              p.getArguments())) 

"""
Remaining API calls are dealt with individually, below.
"""     
urlpatterns += patterns(
    '',
    # Homepage
    (r'^$', home),
    
    # OAuth
    (r'^oauth/', include('smart.urls.oauth')),
    
    (r'^version$', get_version),

    (r'^accounts/search$', account_search),
    (r'^accounts/(?P<account_email>[^/]+)$', account_info),
    (r'^accounts/(?P<account_email>[^/]+)/recent_records/$', account_recent_records),
    (r'^accounts/(?P<account_email>[^/]+)/', include('smart.urls.account')),


    #Capabilities    
    (r'^capabilities/$', MethodDispatcher({
                         'GET': container_capabilities,
                         'OPTIONS' : allow_options})),

    # Record
    (r'^record_by_token/$', record_by_token),
    (r'^records/search/$', record_search),
    (r'^records/(?P<record_id>[^/]+)$', record_info),

    (r'^records/(?P<record_id>[^/]+)/demographics$', MethodDispatcher({
                                       'GET': record_get_all_objects,
                                       'POST': record_demographics_put,
                                       'PUT': record_demographics_put,
                                       'OPTIONS' : allow_options}),
                                       {'obj_type' : 'http://xmlns.com/foaf/0.1/Person'}),


    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': add_app,
                'DELETE': remove_app})),
                
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<pha_email>[^/]+)/records/(?P<record_id>[^/]+)/launch$', launch_app),
    
    # PHAs
    (r'^apps/$', all_phas),
    (r'^apps/accounts/(?P<account_id>[^/]+)/$', apps_for_account),
    (r'^activity/(?P<activity_name>[^/]+)/app/(?P<app_id>[^/]+)$', resolve_activity_with_app),
    (r'^activity/(?P<activity_name>[^/]+)$', resolve_activity),
    
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/first$', get_first_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)/next$', get_next_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)$', get_record_tokens),
    
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),

    # SMArt API
    (r'^app_storage/(?P<pha_email>[^/]+)/$', MethodDispatcher({
                                       'GET': pha_storage_get,
                                       'POST': pha_storage_post,
                                       'DELETE': pha_storage_delete,
                                       'OPTIONS' : allow_options})),


    # SMArt webhook API
    (r'^webhook/(?P<webhook_name>[^/]+)$', MethodDispatcher({
                                       'GET': do_webhook,
                                       'POST': do_webhook,
                                       'OPTIONS' : allow_options})),

      # SMArt users API    
    (r'^users/search$', MethodDispatcher({
                                       'GET': user_search,
                                       'OPTIONS' : allow_options})),
                                       

    # SMArt webhook API
    (r'^users/(?P<user_id>[^/]+)$', MethodDispatcher({
                                       'GET': user_get,
                                       'OPTIONS' : allow_options})),
                                       

    (r'^users/$', MethodDispatcher({
                                       'POST': user_create,
                                       'OPTIONS' : allow_options})),

    # SMArt ontology
    (r'^ontology/$', MethodDispatcher({
                                       'GET': download_ontology,
                                       'OPTIONS' : allow_options})),

  
  )