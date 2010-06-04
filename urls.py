from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
     # Everything to indivo
    (r'^', include('smart_server.smart.urls.urls')),
)
