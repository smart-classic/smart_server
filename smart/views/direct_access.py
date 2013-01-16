"""
Support for adding records and generating direct-access URLs tied to
these records.  This functionality supports two use cases:

 * SMART Direct Proxy Server, which receives patient record data via
   Direct Project messages and creates new patient records on the fly,
   each with a direct-access URL

 * SMART Reference EMR in "Proxy" mode, where authentication is
   handled by a component in front of the proxy.

Josh Mandel
"""

from base import *
from smart.lib import utils
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from smart.models import *
import datetime


def create_proxied_record(request):
    record_id = request.POST['record_id']
    record_name = request.POST['record_name']
    r, created = Record.objects.get_or_create(
        id=record_id, defaults={'full_name': record_name}
    )
    if not created and r.full_name != record_name:
        r.full_name = record_name
        r.save()

    return DONE


# Pluggable support for figuring out which user to attach
# to a direct access URL.
class DirectAccessUserMapper(object):
    @classmethod
    def map_user(cls, request, record):
        return Account.objects.get(email=settings.PROXY_USER_ID)

    @classmethod
    def register(cls, new_registrant):
        cls.map_user = classmethod(new_registrant)
        return


@paramloader()
def generate_direct_url(request, record):
    r = Record.objects.get(id=record.id)

    # For some use cases, may want to replace this with a throwaway user
    account = DirectAccessUserMapper.map_user(request, record)

    p = request.GET.get("pin", None)

    if account.is_active:
        t = r.generate_direct_access_token(account=account, token_secret=p)
        return_url = settings.SMART_UI_SERVER_LOCATION + "/token/" + t.token
        return HttpResponse(return_url, mimetype='text/plain')

    else:
        print "Nonactive", account
    return DONE


def session_from_direct_url(request):
    token = request.GET['token']
    p = request.GET.get("pin", None)

    login_token = RecordDirectAccessToken.objects.get(token=token)
    if (login_token.token_secret != p):
        raise PermissionDenied("Wrong pin for token")

    # TODO: move this to security function on chrome consumer
    if (datetime.datetime.utcnow() > login_token.expires_at):
        return HttpResponseForbidden("Expired token %s" % token)

    session_token = SESSION_OAUTH_SERVER.generate_and_preauthorize_access_token(request.principal, user=login_token.account)
    session_token.save()

    return render_template('login_token', {'record': login_token.record, 'token': str(session_token)}, type='xml')
