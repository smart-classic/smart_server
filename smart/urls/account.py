from django.conf.urls.defaults import *

from smart.views import *
from smart.lib.utils import MethodDispatcher

urlpatterns = patterns(
    '',

    # reset
    (r'^reset$', account_reset),

    # auth systems
    (r'^authsystems/$', MethodDispatcher({
                'POST' : account_authsystem_add})),

    # change the password
    (r'^authsystems/password/change$', MethodDispatcher({
                'POST' : account_password_change})),

    # set the password
    (r'^authsystems/password/set$', MethodDispatcher({
                'POST' : account_password_set})),

    # URL to initialize account
    (r'^initialize/(?P<primary_secret>[^/]+)$', MethodDispatcher({
                'POST' : account_initialize})),

    # URL to resend the login URL
    (r'^secret-resend$', account_resend_secret),
    
    # secret
    (r'^secret$', account_secret),

    # primary secret (very limited call)
    (r'^primary-secret$', account_primary_secret),

    # record list
    (r'^records/$', record_list),


    (r'^records/$', MethodDispatcher({
                'GET' : record_list
                })), 
)    
