""" Indivo Views """

VERSION = '0.0.1'

from base import *
from pha import *
from account import *
from smarthacks import *
from direct_access import *
from rdfstore import *

from django.http import HttpResponse
def get_version(request): return HttpResponse(VERSION, mimetype="text/plain")
