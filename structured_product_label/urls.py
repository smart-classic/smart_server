from django.conf.urls.defaults import *
from django.conf import settings
from smart.lib.utils import MethodDispatcher
from views import *
from smart.views.smarthacks import allow_options
import os

urlpatterns = patterns('',
    (r'^for_rxnorm/(?P<rxn_concept>[^/]+)$', MethodDispatcher({
                                       'GET': spl_view,
                                       'OPTIONS' : allow_options})),
    
    (r'^data/(?P<path>.*)$', 'django.views.static.serve', 
            {'document_root': os.path.join(settings.APP_HOME,
                                           'structured_product_label/data')})

)

