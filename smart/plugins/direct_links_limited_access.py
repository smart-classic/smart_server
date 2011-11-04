from django.conf import settings

from smart.views import *
from smart.models import *
from smart.lib import utils
from smart.models.accounts import ACTIVE

@DirectAccessUserMapper.register
def map_user(cls, request, record):
    e =  utils.random_string(30) + "@anonymous.smartplatforms.org"

    a = LimitedAccount.objects.create(email=e, 
                               given_name="Anomymous", 
                               family_name="Account")
    a.set_state(ACTIVE)
    a.records.add(record)
    a.save()
    return a
