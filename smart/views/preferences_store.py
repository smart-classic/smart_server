from smart.models import *
from base import utils
from django.http import HttpResponse
from smart.models.ontology_url_patterns import CallMapper


@CallMapper.register(client_method_name="put_user_preferences")
def preferences_put(request, user_id, pha_email):
    try:
        ct = utils.get_content_type(request).lower().split(';')[0]
        if (not ct) or len(ct) == 0 or ct == "none":
            ct = "text/plain"
    except:
        ct = "text/plain"

    p = fetch_preferences(user_id, pha_email)
    p.data = request.raw_post_data
    p.mime = ct
    p.save()
    return HttpResponse(p.data, mimetype=p.mime)


@CallMapper.register(client_method_name="get_user_preferences")
def preferences_get(request, user_id, pha_email):
    p = fetch_preferences(user_id, pha_email)
    return HttpResponse(p.data, mimetype=p.mime)


@CallMapper.register(client_method_name="delete_user_preferences")
def preferences_delete(request, user_id, pha_email):
    p = fetch_preferences(user_id, pha_email)
    p.delete()
    return HttpResponse("ok")


def resolve_account_pha(user_id, pha_email):
    account = None
    pha = None

    if user_id is not None:
        try:
            account = Account.objects.get(email=user_id)
        except Account.DoesNotExist:
            pass

    if pha_email is not None:
        try:
            pha = PHA.objects.get(email=pha_email)
        except PHA.DoesNotExist:
            pass

    return account, pha


def fetch_preferences(user_id, pha_email):
    account, pha = resolve_account_pha(user_id, pha_email)
    pref_obj = Preferences.objects.get_or_create(
        account=account,
        pha=pha,
        defaults={
            "data": "",
            "mime": "text/plain"
        }
    )
    return pref_obj[0]
