""" Indivo Views """

VERSION = '0.8.2.1'

from base    import *

from django.http import HttpResponse
def get_version(request): return HttpResponse(VERSION, mimetype="text/plain")
