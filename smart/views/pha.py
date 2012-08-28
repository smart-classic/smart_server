"""
Indivo views -- PHAs
"""

import urllib
import urlparse

from base import *
from django.utils import simplejson

from smart.accesscontrol.oauth_servers import OAUTH_SERVER, SESSION_OAUTH_SERVER
from smart.models.ontology_url_patterns import CallMapper

from oauth.djangoutils import extract_request
from oauth import oauth

from smart.accesscontrol import auth
from smart.lib import iso8601
import base64
import hmac
import datetime


def all_phas(request):
    """A list of the PHAs as XML"""
    phas = [PHA.objects.get(id=x.app.id) for x in AppActivity.objects.filter(name="main")]
    return render_template('phas', {'phas': phas}, type="xml")


@CallMapper.register(method="GET",
                     category="container_items",
                     target="http://smartplatforms.org/terms#AppManifest")
def all_manifests(request):
    """A list of the PHAs as JSON"""
    phas = [PHA.objects.get(id=x.app.id) for x in AppActivity.objects.filter(name="main")]
    ret = "[" +", ".join([a.manifest for a in phas])+ "]"
    return HttpResponse(ret, mimetype='application/json')


@CallMapper.register(method="GET",
                     category="container_item",
                     target="http://smartplatforms.org/terms#AppManifest")
def resolve_manifest(request, descriptor):
    if "@" in descriptor:
        return resolve_manifest_with_app(request, "main", descriptor)
    else:
        return resolve_manifest_with_app(request, descriptor, None)


def resolve_manifest_with_app(request, activity_name, app_id):
    act = resolve_activity_helper(request, activity_name, app_id)
    if act == None:
        raise Http404
    
    manifest = act.app.manifest
    if (act.remapped):
        manifest = simplejson.loads(manifest)
        manifest['index'] = act.url
        manifest = simplejson.dumps(manifest)
    
    return HttpResponse(manifest, mimetype='application/json')


def resolve_activity(request, activity_name):
    return resolve_activity_with_app(request, activity_name, None)


def resolve_activity_with_app(request, activity_name, app_id):
    act = resolve_activity_helper(request, activity_name, app_id)
    return render_template('activity', {'a': act}, type="xml")


def resolve_activity_helper(request, activity_name, app_id):
    """ Map an activity name (and optionally specified app id) to activity URL.
    """
    act = None
    
    if (app_id != None):
        act = AppActivity.objects.filter(name=activity_name, app__email=app_id)
    else:
        act = AppActivity.objects.filter(name=activity_name)
    
    if len(act) == 0: 
        return None
  
    act = act[0]
 
    if (act.url == None):
        act.url = PHA.objects.get(id=act.app.id).start_url_template
        act.url = PHA.objects.get(id=act.app.id).start_url_template
    
    try:
        r = PrincipalActivityRemaps.objects.get(activity=act, principal=request.principal)
        act.url = r.url
        act.remapped = True
        print "remapping for principal %s: %s", (request.principal, act.url) 
    
    except:
        act.remapped = False
    
    print "mapped ", request.principal, activity_name, app_id, " to: ", act
    return act


def pha(request, pha_email):
    try:
        pha = PHA.objects.get(id=pha_email)
        return render_template('pha', {'pha' : pha}, type="xml")
    except:
        raise Http404


def app_oauth_credentials(request, app_id):
    """ Return the OAuth credentials for the given app.
    Must be a machine app to perform this call.
    """
    app = PHA.objects.get(email=app_id)
    json = {
        'consumer_key': app.email,              # Is email really what's used as key?
        'consumer_secret': app.secret
    }
    return HttpResponse(simplejson.dumps(json), mimetype='application/json')


##
## OAuth Process
##
def request_token(request):
    """ Get a new request token, bound to a record if desired.

    request.POST may contain:

    * *smart_record_id*: The record to which to bind the request token.

    Will return :http:statuscode:`200` with the request token on success,
    :http:statuscode:`403` if the oauth signature on the request was missing
    or faulty.
    Will raise on bad signature.
    """
    # ask the oauth server to generate a request token given the HTTP request
    try:
        # we already have the oauth_request in context, so we don't get it again
        app = request.principal
        request_token = OAUTH_SERVER.generate_request_token(
            request.oauth_request, 
            record_id = request.POST.get('smart_record_id', None),
            offline_capable = request.POST.get('offline', False)
        )

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
    username = request.POST.get('username')
    password = request.POST.get('password')
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
    try:
        rt = ReqToken.objects.get(token = request_token)
    except models.ReqToken.DoesNotExist:
        raise PermissionDenied()
    
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
    
    record_id = request.POST.get('record_id')
    offline = request.POST.get('offline', False)
    
    # requesting offline but request token doesn't allow it? Bust!
    if offline and not rt.offline_capable:
        raise PermissionDenied
    
    # different record id? You wish!
    if (record_id and rt.record and record_id != rt.record.record_id):
        raise PermissionDenied("Request token pre-bound record %s doesn't match post variable %s" % (rt.record.record_id, record_id))
    
    # no record reference at all? Crash and burn
    if (not (rt.record or record_id)):
        raise Exception("Must have a record bound to token or a record_id passed in to authorize.")
    
    record = rt.record
    if not record: 
        record = Record.objects.get(id=record_id)
    
    # authorize the request token
    request_token = OAUTH_SERVER.authorize_request_token(rt.token, record=record, account=request.principal, offline=offline)
    
    # respond with a redirect
    # TODO (pp, 7/12/2012): The app does not yet have a 'callback_url' property,
    # for now this will crash if no oauth_callback is supplied. Providing an
    # oauth_callback may NOT be supported however, so adjust the following line
    # as needed
    redirect_url = request_token.oauth_callback or request_token.app.callback_url
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
