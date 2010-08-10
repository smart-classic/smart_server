"""
Views for coding systems

ben.adida@childrens.harvard.edu
2009-11-12
"""

from smart.lib.utils import *
from models import *
from django.http import *

def spl_view(request, rxn_concept):
    r = SPL_from_rxn_concept(rxn_concept)
    return HttpResponse(r.toRDF(), mimetype="text/plain")