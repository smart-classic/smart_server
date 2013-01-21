from smart.models import *
from base import utils
from django.http import HttpResponse
from smart.models.ontology_url_patterns import CallMapper

@CallMapper.register(client_method_name="put_user_preferences")
def preferences_put (request, user_id, pha_email):
    try:
        ct = utils.get_content_type(request).lower().split(';')[0]
        if (not ct) or len(ct) == 0 or ct == "none": ct = "text/plain"
    except:
        ct = "text/plain"

    p = fetch_preferences (user_id, pha_email)
    p.data = request.raw_post_data
    p.mime = ct
    p.save()
    return HttpResponse(p.data, mimetype=p.mime)

@CallMapper.register(client_method_name="get_user_preferences")
def preferences_get (request, user_id, pha_email):   
    p = fetch_preferences (user_id, pha_email)
    return HttpResponse(p.data, mimetype=p.mime)

@CallMapper.register(client_method_name="delete_user_preferences")
def preferences_delete(request, user_id, pha_email): 
    p = fetch_preferences (user_id, pha_email)
    p.delete()
    return HttpResponse("ok")
    
@CallMapper.register(client_method_name="put_scratchpad_data")
def scratchpad_put (request, record_id, pha_email):
    try:
        ct = utils.get_content_type(request).lower().split(';')[0]
        if (not ct) or len(ct) == 0 or ct == "none": ct = "text/plain"
    except:
        ct = "text/plain"

    p = fetch_scratchpad (record_id, pha_email)
    p.data = request.raw_post_data
    p.mime = ct
    p.save()
    return HttpResponse(p.data, mimetype=p.mime)

@CallMapper.register(client_method_name="get_scratchpad_data")
def scratchpad_get (request, record_id, pha_email):   
    p = fetch_scratchpad (record_id, pha_email)
    return HttpResponse(p.data, mimetype=p.mime)

@CallMapper.register(client_method_name="delete_scratchpad_data")
def scratchpad_delete(request, record_id, pha_email): 
    p = fetch_scratchpad (record_id, pha_email)
    p.delete()
    return HttpResponse("ok")  


def resolve_account (user_id):
    account = None
    
    if user_id != None: 
        try:
            account = Account.objects.get(email=user_id)
        except Account.DoesNotExist:
            pass
    
    return account
    
def resolve_pha (pha_email):
    pha = None
            
    if pha_email != None:
        try:
            pha = PHA.objects.get(email=pha_email)
        except PHA.DoesNotExist:
            pass
    
    return pha
    
def resolve_record (record_id):
    record = None
    
    if record_id != None: 
        try:
            record = Record.objects.get(id=record_id)
        except Record.DoesNotExist:
            pass
    
    return record
    
def fetch_preferences(user_id, pha_email):
    account = resolve_account (user_id)
    pha = resolve_pha (pha_email)
    return Store.objects.get_or_create(pha=pha, account=account, record=None, defaults={"data": "", "mime": "text/plain"})[0]
    
def fetch_scratchpad (record_id, pha_email):
    record = resolve_record (record_id)
    pha = resolve_pha (pha_email)
    return Store.objects.get_or_create(pha=pha, account=None, record=record, defaults={"data": "", "mime": "text/plain"})[0]
