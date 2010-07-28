"""
Views for coding systems

ben.adida@childrens.harvard.edu
2009-11-12
"""

from smart.lib.utils import *
from models import *
from django.http import *

def coding_systems_list(request):
    pass

@django_json
def coding_system_query(request, system_short_name):
    try:
        coding_system = CodingSystem.objects.get(short_name = system_short_name)
    except CodingSystem.DoesNotExist:
        raise Http404

    return [c.toJSONDict() for c in coding_system.search_codes(request.GET['q'], limit = 100)]
