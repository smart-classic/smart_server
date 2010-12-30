from django.conf.urls.defaults import include, patterns
from smart.views import *
from smart.models.ontology_url_patterns import OntologyURLMapper

urlpatterns = patterns('')

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

    # Record
    (r'^record_by_token/$', record_by_token),
    (r'^records/search/$', record_search),
    (r'^records/(?P<record_id>[^/]+)$', record_info),

    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': add_app,
                'DELETE': remove_app})),
                
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<pha_email>[^/]+)/records/(?P<record_id>[^/]+)/launch$', launch_app),
    
    (r'^users/$', MethodDispatcher({ 'POST': user_create,'OPTIONS' : allow_options})),
    (r'^users/reset_password_request$', MethodDispatcher({'POST': user_reset_password_request})),
    (r'^users/reset_password$', MethodDispatcher({'POST': user_reset_password})),

    
    # PHAs
    (r'^apps/$', all_phas),
    (r'^apps/accounts/(?P<account_id>[^/]+)/$', apps_for_account),
    (r'^activity/(?P<activity_name>[^/]+)/app/(?P<app_id>[^/]+)$', resolve_activity_with_app),
    (r'^activity/(?P<activity_name>[^/]+)$', resolve_activity),
    
    # static
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),

    # SMArt API
    (r'^app_storage/(?P<pha_email>[^/]+)/$', MethodDispatcher({
                                       'GET': pha_storage_get,
                                       'POST': pha_storage_post,
                                       'DELETE': pha_storage_delete,
                                       'OPTIONS' : allow_options})),


    (r'^webhook/(?P<webhook_name>[^/]+)$', MethodDispatcher({
                                       'GET': do_webhook,
                                       'POST': do_webhook,
                                       'OPTIONS' : allow_options})),  

    (r'^apps/(?P<app_email>[^/]+)/tokens/records/first$', get_first_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)/next$', get_next_record_tokens),
    (r'^apps/(?P<app_email>[^/]+)/tokens/records/(?P<record_id>[^/]+)$', get_record_tokens),

    (r'^accounts/search$', account_search),
    (r'^accounts/(?P<account_email>[^/]+)$', account_info),
    (r'^accounts/(?P<account_email>[^/]+)/recent_records/$', account_recent_records),
    (r'^accounts/(?P<account_email>[^/]+)/', include('smart.urls.account')),    
  )

"""
Record objects (meds, fills, notes, problems, etc.) are handled (when possible)
in an ontology-driven way:  rdfobjects loads the ontology, registers
handlers for all the relevant paths (e.g. /records/{record_id}/medications/)
and specified methods (GET, POST, PUT, DELETE).
"""

ontology["http://xmlns.com/foaf/0.1/Person"].put = put_demographics
ontology["http://smartplatforms.org/terms#User"].get_one = user_get
ontology["http://smartplatforms.org/terms#User"].get_all = user_search
ontology["http://smartplatforms.org/terms#Container"].get_all = container_capabilities
ontology["http://smartplatforms.org/terms#Ontology"].get_one = download_ontology

m =  OntologyURLMapper() 
for p, calls in m.calls_by_path():
    urlpatterns += patterns( '',
                             (m.django_path(calls),  
                              MethodDispatcher(m.getMethods(calls)), 
                              m.getArguments(calls)))
