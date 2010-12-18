"""
SMArt (simplified)
Indivo views for Account
"""

from base import *
import urllib
from smart.lib import utils
from smart.lib.utils import smart_base
from django.http import HttpResponseBadRequest, HttpResponseNotFound

ACTIVE_STATE, UNINITIALIZED_STATE = 'active', 'uninitialized'
HTTP_METHOD_GET = 'GET'

def get_id(request):
  principal = request.principal
  
  if principal:
    id = principal.email
  else:
    id = ""
  return render_template('account_id', {'id': id})

@paramloader()
def account_password_change(request, account):
  OLD = 'old'
  NEW = 'new'
  if request.POST.has_key(OLD) and request.POST.has_key(NEW):
    if account.password_check(request.POST[OLD]):
      account.password = request.POST[NEW]
      account.save()
    return DONE
  return HttpResponseBadRequest()

@paramloader()
def account_reset(request, account):
  account.reset()
  return DONE

@paramloader()
def account_password_set(request, account):
  if request.POST.has_key('password'):
    account.password = request.POST['password']
    account.save()
    return DONE
  return HttpResponseBadRequest()

@paramloader()
@transaction.commit_on_success
def account_initialize(request, account, primary_secret):
  SECONDARY_SECRET = 'secondary_secret'

  # check primary secret
  if account.primary_secret != primary_secret:
    account.on_failed_login()
    raise PermissionDenied()

  if account.state != UNINITIALIZED_STATE:
    raise PermissionDenied()
  
  # if there is a secondary secret in the account, check it in the form
  if request.POST.has_key(SECONDARY_SECRET):
    secondary_secret = request.POST[SECONDARY_SECRET]
    if account.secondary_secret and secondary_secret != account.secondary_secret:
      account.on_failed_login()
      raise PermissionDenied()

    account.state = ACTIVE_STATE
    account.send_welcome_email()
    account.save()

    return DONE
  return HttpResponseBadRequest()

@paramloader()
def account_primary_secret(request, account):
  return render_template('secret', {'secret':account.primary_secret})

@paramloader()
def account_info(request, account):
  # get the account auth systems
  auth_systems = account.auth_systems.all()
  return render_template('account', { 'account'       : account,
                                      'auth_systems'  : auth_systems }, type='xml')

def account_search(request):
  """Search accounts"""

  fullname      = request.GET.get('fullname', None)
  contact_email = request.GET.get('contact_email', None)

  if not (fullname or contact_email):
    # SZ: This exception needs to be more explicit
    raise Exception("one criteria needed")

  res = []
  if fullname or contact_email:
    res = Account.objects.filter(fullname = fullname) or \
          Account.objects.filter(contact_email = contact_email)
  return render_template('accounts_search', {'accounts': res}, type='xml')

@paramloader()
def account_authsystem_add(request, account):
  try:
    system = AuthSystem.objects.get(short_name = request.POST['system'])
  except AuthSystem.DoesNotExist:
    raise PermissionDenied()
  system, created_p = account.auth_systems.get_or_create(auth_system= system, username=request.POST['username'])
  if system.auth_system == AuthSystem.PASSWORD() and created_p and request.POST.has_key('password'):
    account.password_set(request.POST['password'])
    account.set_state(ACTIVE_STATE)
    account.save()

  # return the account info instead
  return DONE

@paramloader()
def account_resend_secret(request, account):
  # FIXME: eventually check the status of the account
  account.send_secret()
  
  # probably ok to return DONE, but it should just be empty, like Flickr
  return DONE
  
@paramloader()
def account_secret(request, account):
  return HttpResponse("<secret>%s</secret>" % account.secondary_secret)

@transaction.commit_on_success
def user_create(request):
  """Create an account"""

  account_id = request.POST.get('account_id', None)
  print "CREATING for", account_id
  if not account_id or not utils.is_valid_email(account_id):
    return HttpResponseBadRequest("Account ID not valid")

  new_account, create_p = Account.objects.get_or_create(email=urllib.unquote(account_id))

  if not create_p:
    return HttpResponse("account_exists")

  if create_p:
    """
    generate a secondary secret or not? Requestor can say no.
    trust model makes sense: the admin app requestor only decides whether or not 
    they control the additional interaction or if it's not necessary. They never
    see the primary secret.
    """

    new_account.given_name = request.POST.get('given_name', '')
    new_account.family_name = request.POST.get('family_name', '')
    new_account.department = request.POST.get('department', 'any')
    new_account.role = request.POST.get('role', 'any')

    # FIXME: do we really want a contact email to be account_id?
    new_account.contact_email = request.POST.get('contact_email', account_id)

    primary_secret_p = (request.POST.get('primary_secret_p', "0") == "1")
    secondary_secret_p = (request.POST.get('secondary_secret_p', "0") == "1")
    password = request.POST.get('password', None)
    new_account.creator = request.principal

    # set password if need be
    #SZ: if not secondary_secret_p and password:
    if not primary_secret_p and not secondary_secret_p and password:
      new_account.set_username_and_password(account_id, password)

    new_account.save()

    #SZ: if password and len(password) > 0:
    if primary_secret_p:
      new_account.generate_secrets(secondary_secret_p = secondary_secret_p)
      new_account.send_secret()

  return render_template('account', {'account' : new_account}, type='xml')

def user_reset_password_request(request):
    email = request.POST.get('account_email', None)
    try:
        a = Account.objects.get(email=email)
    except:
        return HttpResponse("no_account_exists")

    a.forgot_password()
    return render_template('account', {'account' : a}, type='xml')
  
def user_reset_password(request):
    email = request.POST.get('account_email', None)
    secret = request.POST.get('account_secret', None)
    new_password = request.POST.get('new_password', None)
    
    if email == None or secret == None or new_password == None:   
        return HttpResponseBadRequest()
    
    try:
        a = Account.objects.get(email=email, primary_secret=secret)
        a.password = new_password
        a.generate_secrets()
        return render_template('account', {'account' : a}, type='xml')

    except: return HttpResponseBadRequest()
  
def user_get(request, user_id, **kwargs):
    try:
        a = Account.objects.get(email=user_id)
        m = a.to_rdf()
    except: return HttpResponseNotFound()
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))

def user_search(request, **kwargs):
    aa = Account.objects.all()

    m = RDF.Model()
    
    f  = request.GET.get("givenName", None)
    l  = request.GET.get("familyName", None)
    d  = request.GET.get("department", None)
    r  = request.GET.get("role", None)
    
    if (f != None): aa = aa.filter(given_name__icontains=f)
    if (l != None): aa = aa.filter(family_name__icontains=l)
    if (d != None): aa = aa.filter(department__icontains=d)
    if (r != None): aa = aa.filter(role__icontains=r)
    
    for a in aa:
        print "Adding ", a.email, a.given_name, a.family_name
        a.to_rdf(m)
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))