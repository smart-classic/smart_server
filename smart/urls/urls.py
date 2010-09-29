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


    #Capabilities    
    (r'^capabilities/$', MethodDispatcher({
                         'GET': container_capabilities,
                         'OPTIONS' : allow_options})),

    # Record
    (r'^record_by_token/$', record_by_token),
    (r'^records/search/$', record_search),
    (r'^records/(?P<record_id>[^/]+)$', record_info),

    
    (r'^records/(?P<record_id>[^/]+)/sparql$', MethodDispatcher({
                                       'GET': record_sparql,
                                       'OPTIONS' : allow_options})),
                                       
    (r'^records/(?P<record_id>[^/]+)/medications/$', MethodDispatcher({
                                       'GET': record_meds_get,
                                       'POST': record_meds_post,
                                       'DELETE': record_meds_delete,
                                       'OPTIONS' : allow_options})),
                                       
    (r'^records/(?P<record_id>[^/]+)/medications/(?P<med_id>[^/]+)$',  MethodDispatcher({
                                       'GET': record_med_get,
                                       #'PUT': record_med_put,
                                       'POST': record_med_post,
                                       'DELETE': record_med_delete,
                                       'OPTIONS' : allow_options})),


    (r'^records/(?P<record_id>[^/]+)/medications/external_id/(?P<external_id>[^/]+)$',  
                                    MethodDispatcher({
                                       'PUT': record_med_put,
                                       'GET': record_med_get_external,
                                       'DELETE': record_med_delete_external,
                                       'OPTIONS' : allow_options})),
#    
    (r'^records/(?P<record_id>[^/]+)/medications/(?P<med_id>[^/]+)/fulfillments/$',  MethodDispatcher({
                                       'GET': record_med_fulfillments_get,
                                       'DELETE': record_med_fulfillments_delete,
                                       'POST': record_med_fulfillments_post,
                                       'OPTIONS' : allow_options})),
#                                       
    (r'^records/(?P<record_id>[^/]+)/medications/(?P<med_id>[^/]+)/fulfillments/(?P<fill_id>[^/]+)$',   MethodDispatcher({
                                       'GET': record_med_fulfillment_get,
                                       'DELETE': record_med_fulfillment_delete,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/medications/external_id/(?P<external_med_id>[^/]+)/fulfillments/external_id/(?P<external_fill_id>[^/]+)$',   MethodDispatcher({
                                       'GET': record_med_fulfillment_get_external,
                                       'DELETE': record_med_fulfillment_delete_external,
                                       'PUT': record_med_fulfillment_put_external,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/problems/$', MethodDispatcher({
                                       'GET': record_problems_get,
                                       'POST': record_problems_post,
                                       'DELETE': record_problems_delete,
                                       'OPTIONS' : allow_options})),
#                                       
    (r'^records/(?P<record_id>[^/]+)/problems/(?P<problem_id>[^/]+)$', MethodDispatcher({
                                       'GET': record_problem_get,
                                       'DELETE': record_problem_delete,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/problems/external_id/(?P<external_id>[^/]+)$',  
                                    MethodDispatcher({
                                       'PUT': record_problem_put,
                                       'GET': record_problem_get_external,
                                       'DELETE': record_problem_delete_external,
                                       'OPTIONS' : allow_options})),


    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)$', MethodDispatcher({
                'PUT': add_app,
                'DELETE': remove_app})),
                
    (r'^accounts/(?P<account_id>[^/]+)/apps/(?P<app_email>[^/]+)/records/(?P<record_id>[^/]+)/launch$', launch_app),
    
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

    # SMArt webhook API
    (r'^webhook/(?P<webhook_name>[^/]+)$', MethodDispatcher({
                                       'GET': do_webhook,
                                       'POST': do_webhook,
                                       'OPTIONS' : allow_options}))

  
  )

