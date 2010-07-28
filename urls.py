from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Coding Systems
    (r'^codes/', include('smart_server.codingsystems.urls')),

     # Everything to indivo
    (r'^', include('smart_server.smart.urls.urls')),
)
