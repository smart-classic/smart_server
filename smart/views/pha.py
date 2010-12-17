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
  phas = [PHA.objects.get(id=x.app.id) for x in AppActivity.objects.filter(name="main")]
  return render_template('phas', {'phas': phas}, type="xml")


def resolve_activity(request, activity_name):
    return resolve_activity_with_app(request, activity_name, None)

def resolve_activity_with_app(request, activity_name, app_id):
  """Map an activity name (and optionally specified app id) to activity URL."""
  act = None
  
  if (app_id != None):
      act = AppActivity.objects.filter(name=activity_name, app__email=app_id)[0]
  else:
      act = AppActivity.objects.filter(name=activity_name)[0]
      
  print "mapped ", activity_name, app_id, " to: ", act
  if (act.url == None):
    act.url = PHA.objects.get(id=act.app.id).start_url_template
    
  return render_template('activity', {'a': act}, type="xml")

  
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

      app = request.principal
      request_token = OAUTH_SERVER.generate_request_token(request.oauth_request, 
                                                          record_id = request.POST.get('record_id', None),
                                                          offline_capable = request.POST.get('offline', False))
      
      return HttpResponse(request_token.to_string(), mimetype='text/plain')
    except oauth.OAuthError, e:
      
      import sys, traceback
      traceback.print_exc(file=sys.stderr)
    
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
      share = Share.objects.get(record= rt.record, with_app = rt.app,authorized_by=request.principal)
  except Share.DoesNotExist:
    pass

  return render_template('requesttoken', {'request_token':rt, 'share' : share}, type='xml')

@paramloader()
def request_token_approve(request, request_token):
  rt = ReqToken.objects.get(token = request_token)

  record_id=request.POST.get('record_id', None)
  offline = request.POST.get('offline', False)

  # requesting offline but request token doesn't allow it? Bust!
  if offline and not rt.offline_capable:
    raise PermissionDenied

  record = rt.record

  if (record_id and rt.record and record_id != rt.record.record_id):
    raise PermissionDenied("Request token pre-bound record %s != post variable %s"%(record.record_id, record_id))

  if (not (rt.record or record_id)):
    raise Exception("Must have a record bound to token or a record_id passed in to authorize.")

  if not record: 
    record = Record.objects.get(id=record_id)

  # authorize the request token
  request_token = OAUTH_SERVER.authorize_request_token(rt.token, record=record, account = request.principal, offline = offline)

  # where to redirect to + parameters
  redirect_url = AppActivity.objects.get(app=request_token.app, name="after_auth").url
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
