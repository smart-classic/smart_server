from smart.models import *
from base import utils
from django.http import HttpResponse

def preferences_put (request, account_email, pha_email):
    try:
        ct = utils.get_content_type(request).lower().split(';')[0]
        if (not ct) or len(ct) == 0 or ct == "none": ct = "text/plain"
    except:
        ct = "text/plain"

    p = fetch_preferences (account_email, pha_email)
    p.data = request.raw_post_data
    p.mime = ct
    p.save()
    return HttpResponse("ok")

def preferences_get (request, account_email, pha_email):   
    p = fetch_preferences (account_email, pha_email)
    return HttpResponse(p.data, mimetype=p.mime)

def preferences_delete(request, account_email, pha_email): 
    p = fetch_preferences (account_email, pha_email)
    p.delete()
    return HttpResponse("ok")  

def resolve_account_pha (account_email, pha_email):
    account = None
    pha = None
    
    if account_email != None: 
        try:
            account = Account.objects.get(email=account_email)
        except Account.DoesNotExist:
            pass
            
    if pha_email != None:
        try:
            pha = PHA.objects.get(email=pha_email)
        except PHA.DoesNotExist:
            pass
    
    return account, pha
    
def fetch_preferences(account_email, pha_email):
    account, pha = resolve_account_pha (account_email, pha_email)
    return Preferences.objects.get_or_create(account=account, pha=pha, defaults={"data": "", "mime": "text/plain"})[0]