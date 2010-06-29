"""
Indivo views -- PHAs
"""

import urllib, urlparse

from base import *

from smart.accesscontrol.oauth_servers import OAUTH_SERVER, SESSION_OAUTH_SERVER
from oauth.djangoutils import extract_request
from oauth import oauth

from smart.accesscontrol import auth
from smart.lib import iso8601
import base64, hmac, datetime

def all_phas(request):
  """A list of the PHAs as JSON"""

  phas = PHA.objects.all()
  return render_template('phas', {'phas': phas}, type="xml")
  
def pha(request, pha_email):
  try:
    pha = PHA.objects.get(id = pha_email)
    return render_template('pha', {'pha' : pha}, type="xml")
  except:
    raise Http404

  
##
## OAuth Process
##

def request_token(request):
    """
    the request-token request URL
    """
    # ask the oauth server to generate a request token given the HTTP request

    try:
      # we already have the oauth_request in context, so we don't get it again
      request_token = OAUTH_SERVER.generate_request_token(request.oauth_request, 
                                                          record_id = request.POST.get('indivo_record_id', None),
                                                          offline_capable = request.POST.get('offline', False))
      return HttpResponse(request_token.to_string(), mimetype='text/plain')
    except oauth.OAuthError, e:
      # an exception can be raised if there is a bad signature (or no signature) in the request
      raise PermissionDenied()


def exchange_token(request):
    # ask the oauth server to exchange a request token into an access token
    # this will check proper oauth for this action

    try:
      access_token = OAUTH_SERVER.exchange_request_token(request.oauth_request)
      # an exception can be raised if there is a bad signature (or no signature) in the request
    except:
      raise PermissionDenied()

    return HttpResponse(access_token.to_string(), mimetype='text/plain')

def user_authorization(request):
  """Authorize a request token, binding it to a single record.

  A request token *must* be bound to a record before it is approved.
  """

  try:
    token = ReqToken.objects.get(token = request.REQUEST['oauth_token'])
  except ReqToken.DoesNotExist:
    raise Http404

  # are we processing the form
  # OR, is this app already authorized
  if request.method == "POST" or (token.record and token.record.has_pha(token.pha)):
    # get the record from the token
    record = token.record

    # are we dealing with a record already
    if not (record and record.has_pha(token.pha)):
      record = Record.objects.get(id = request.POST['record_id'])
    
      # allowed to administer the record? Needed if the record doesn't have the PHA yet
      if not record.can_admin(request.principal):
        raise Exception("cannot administer this record")

    request_token = OAUTH_SERVER.authorize_request_token(token.token, record = record, account = request.principal, offline=request.POST.get('offline', False))

    # where to redirect to + parameters
    redirect_url = request_token.oauth_callback or request_token.pha.callback_url
    redirect_url += "?oauth_token=%s&oauth_verifier=%s" % (request_token.token, request_token.verifier)

    # redirect to the request token's callback, or if null the PHA's default callback
    return HttpResponseRedirect(redirect_url)
  else:
    records = request.principal.records_administered.all()
    return render_template('authorize', {'token' : token, 'records': records})

##
## OAuth internal calls
##

def session_create(request):
  password = None
  if request.POST.has_key('username'):
    username = request.POST['username']
  if request.POST.has_key('password'):
    password = request.POST['password']
    user = auth.authenticate(request, username, password)

  if not password and request.POST.has_key('system'):
    system = request.POST['system']
    try:
      AuthSystems.objects.get(short_name=system)
      user = auth.authenticate(request, username, None, system)
    except AuthSystems.DoesNotExist:
      raise PermissionDenied()

  if not user:
    raise PermissionDenied()

  if user.is_active:
    # auth worked, created a session based token
    token = SESSION_OAUTH_SERVER.generate_and_preauthorize_access_token(request.principal, user=user)
  else:
    raise PermissionDenied()

  return HttpResponse(str(token), mimetype='text/plain')

@paramloader()
def request_token_claim(request, request_token):
  # FIXME: need a select for update here
  rt = ReqToken.objects.get(token = request_token)

  # already claimed by someone other than me?
  if rt.authorized_by != None and rt.authorized_by != request.principal:
    raise PermissionDenied()

  rt.authorized_by = request.principal
  rt.save()
  return HttpResponse(request.principal.email)

@paramloader()
def request_token_info(request, request_token):
  """
  get info about the request token
  """
  rt = ReqToken.objects.get(token = request_token)
  share = None

  try:
    if rt.record:
      share = Share.objects.get(record = rt.record, with_pha = rt.pha)
  except Share.DoesNotExist:
    pass

  return render_template('requesttoken', {'request_token':rt, 'share' : share}, type='xml')

@paramloader()
def request_token_approve(request, request_token):
  rt = ReqToken.objects.get(token = request_token)

  record_id = request.POST.get('record_id', None)
  offline = request.POST.get('offline', False)

  # requesting offline but request token doesn't allow it? Bust!
  if offline and not rt.offline_capable:
    raise PermissionDenied

  record = None
  if record_id:
    record = Record.objects.get(id = record_id)

  # if the request token was bound to a record, then it must match
  if rt.record != None and rt.record != record:
    raise PermissionDenied()


  # the permission check that the current user is authorized to connect to this record
  
  # authorize the request token
  request_token = OAUTH_SERVER.authorize_request_token(rt.token, record = record,  account = request.principal, offline = offline)

  # where to redirect to + parameters
  redirect_url = request_token.oauth_callback or request_token.pha.callback_url
  redirect_url += "?oauth_token=%s&oauth_verifier=%s" % (request_token.token, request_token.verifier)

  # redirect to the request token's callback, or if null the PHA's default callback
  return HttpResponse(urllib.urlencode({'location': redirect_url}))

def get_long_lived_token(request):
  if request.method != "POST":
    # FIXME probably 405
    raise Http404
  
  # check if current principal is capable of generating a long-lived token
  # may move this to accesscontrol, but this is a bit of an odd call
  principal = request.principal

  if not principal.share.offline:
    raise PermissionDenied

  new_token, new_secret = oauth.generate_token_and_secret()
  long_lived_token = principal.share.new_access_token(new_token, new_secret, account = None)
  
  return HttpResponse(long_lived_token.to_string(), mimetype='text/plain')  
