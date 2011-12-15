from smart.models import *
from base import utils
from django.http import HttpResponse

def preferences_put (request, account_email, pha_email):
    try:
        ct = utils.get_content_type(request).lower().split(';')[0]
        if (not ct) or len(ct) == 0 or ct == "none": ct = "text/plain"
    except:
        ct = "text/plain"

    p = find_preferences (account_email, pha_email)
    if p == None: p = create_preferences (account_email, pha_email)
    p.data = request.raw_post_data
    p.mime = ct
    p.save()
    return HttpResponse("ok")

def preferences_get (request, account_email, pha_email):   
    p = find_preferences (account_email, pha_email)
    data = ""
    mime = "text/plain"
    if p != None: 
        data = p.data
        mime = p.mime
    return HttpResponse(data, mimetype=mime)

def preferences_delete(request, account_email, pha_email): 
    p = find_preferences (account_email, pha_email)
    if p != None: p.delete()
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
    
def create_preferences(account_email, pha_email):
    account, pha = resolve_account_pha (account_email, pha_email)    
    return Preferences(account=account, pha=pha)
    
def find_preferences(account_email, pha_email):
    account, pha = resolve_account_pha (account_email, pha_email)
    
    try:
        return Preferences.objects.get(account=account, pha=pha)
    except Preferences.DoesNotExist:
        return None