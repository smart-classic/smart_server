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
                                       'POST': record_med_post,
                                       'DELETE': record_med_delete,
                                       'OPTIONS' : allow_options})),


    (r'^records/(?P<record_id>[^/]+)/medications/external_id/(?P<external_id>[^/]+)$',  
                                    MethodDispatcher({
                                       'PUT': record_med_put,
                                       'POST': record_med_put,
                                       'GET': record_med_get_external,
                                       'DELETE': record_med_delete_external,
                                       'OPTIONS' : allow_options})),
    
    (r'^records/(?P<record_id>[^/]+)/medications/(?P<med_id>[^/]+)/fulfillments/$',  MethodDispatcher({
                                       'GET': record_med_fulfillments_get,
                                       'DELETE': record_med_fulfillments_delete,
                                       'POST': record_med_fulfillments_post,
                                       'OPTIONS' : allow_options})),
                                       
    (r'^records/(?P<record_id>[^/]+)/medications/(?P<med_id>[^/]+)/fulfillments/(?P<fill_id>[^/]+)$',   MethodDispatcher({
                                       'GET': record_med_fulfillment_get,
                                       'DELETE': record_med_fulfillment_delete,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/medications/external_id/(?P<external_med_id>[^/]+)/fulfillments/external_id/(?P<external_fill_id>[^/]+)$',   MethodDispatcher({
                                       'GET': record_med_fulfillment_get_external,
                                       'DELETE': record_med_fulfillment_delete_external,
                                       'PUT': record_med_fulfillment_put_external,
                                       'POST': record_med_fulfillment_put_external,
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
                                       'POST': record_problem_put,
                                       'GET': record_problem_get_external,
                                       'DELETE': record_problem_delete_external,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/notes/$', MethodDispatcher({
                                       'GET': record_notes_get,
                                       'POST': record_notes_post,
                                       'DELETE': record_notes_delete,
                                       'OPTIONS' : allow_options})),
                                       
    (r'^records/(?P<record_id>[^/]+)/notes/(?P<note_id>[^/]+)$', MethodDispatcher({
                                       'GET': record_note_get,
                                       'DELETE': record_note_delete,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/notes/external_id/(?P<external_id>[^/]+)$',  
                                    MethodDispatcher({
                                       'PUT': record_note_put,
                                       'POST': record_note_put,
                                       'GET': record_note_get_external,
                                       'DELETE': record_note_delete_external,
                                       'OPTIONS' : allow_options})),



    (r'^records/(?P<record_id>[^/]+)/allergies/$', MethodDispatcher({
                                       'GET': record_allergies_get,
                                       'POST': record_allergies_post,
                                       'DELETE': record_allergies_delete,
                                       'OPTIONS' : allow_options})),
                                       
    (r'^records/(?P<record_id>[^/]+)/allergies/(?P<allergy_id>[^/]+)$', MethodDispatcher({
                                       'GET': record_allergy_get,
                                       'DELETE': record_allergy_delete,
                                       'OPTIONS' : allow_options})),

    (r'^records/(?P<record_id>[^/]+)/allergies/external_id/(?P<external_id>[^/]+)$',  
                                    MethodDispatcher({
                                       'PUT': record_allergy_put,
                                       'POST': record_allergy_put,
                                       'GET': record_allergy_get_external,
                                       'DELETE': record_allergy_delete_external,
                                       'OPTIONS' : allow_options})),


    (r'^records/(?P<record_id>[^/]+)/demographics$', MethodDispatcher({
                                       'GET': record_demographics_get,
                                       'POST': record_demographics_put,
                                       'PUT': record_demographics_put,
                                       'OPTIONS' : allow_options})),


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
    (r'^users/search$', MethodDispatcher({
                                       'GET': user_search,
                                       'OPTIONS' : allow_options})),
                                       

    # SMArt webhook API
    (r'^users/(?P<user_id>[^/]+)$', MethodDispatcher({
                                       'GET': user_get,
                                       'OPTIONS' : allow_options})),
                                       


  
  )