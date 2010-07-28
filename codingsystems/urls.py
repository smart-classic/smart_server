from django.conf.urls.defaults import *
from smart.lib.utils import MethodDispatcher
from views import *
from smart.views.smarthacks import allow_options

urlpatterns = patterns('',
    (r'^systems/$', coding_systems_list),

    (r'^systems/(?P<system_short_name>[^/]+)/query', MethodDispatcher({
                                       'GET': coding_system_query,
                                       'OPTIONS' : allow_options}))
)
