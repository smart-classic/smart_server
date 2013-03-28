"""
Indivo views -- PHAs
"""

import urllib
import urlparse

import sys
import traceback

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

from load_tools.load_one_app import LoadAppFromJSON


def _all_apps():
    """ Return all apps (PHA and HelperApp instances) """
    apps = list(PHA.objects.all())
    apps.extend(HelperApp.objects.all())
    return apps

def _find_app(app_id):
    """ Return the app with the given id """
    app = None
    try:
        app = PHA.objects.get(email=app_id)
    except PHA.DoesNotExist:
        try:
            app = HelperApp.objects.get(email=app_id)
        except HelperApp.DoesNotExist:
            return None
    return app
    
    
def all_phas(request):
    """A list of the PHAs as XML"""
    phas = _all_apps()
    return render_template('phas', {'phas': phas}, type="xml")


@CallMapper.register(http_method="GET",
                     cardinality="multiple",
                     target="http://smartplatforms.org/terms#AppManifest")
def all_manifests(request):
    """A list of the PHAs as JSON"""
    phas = _all_apps()
    ret = "[%s]" % ", ".join([a.manifest for a in phas])
    return HttpResponse(ret, mimetype='application/json')


@CallMapper.register(http_method="GET",
                     cardinality="single",
                     target="http://smartplatforms.org/terms#AppManifest")
def resolve_manifest(request, app_id):
    app = _find_app(app_id)
    if app is None:
        raise Http404
    
    return HttpResponse(app.manifest, mimetype='application/json')

def manifest_put(request, app_id):
    try:
        data = request.raw_post_data
        manifest = json.loads(data)
        id = manifest["id"]

        if id == app_id:
            try:
                LoadAppFromJSON(data)
                return HttpResponse("ok")
            except Exception, e:
                return HttpResponse(str(e), status=400)
        else:
            msg = "The manifest id '%s' must match the app id '%s'" % (
                id, app_id)
            print msg
    except:
        pass

    raise Http404


def manifest_delete(request, app_id):
    try:
        app = _find_app(app_id)
        app.delete()
        return HttpResponse("ok")
    except:
        raise Http404


def pha(request, pha_email):
    try:
        pha = PHA.objects.get(id=pha_email)
        return render_template('pha', {'pha': pha}, type="xml")
    except:
        raise Http404


def app_oauth_credentials(request, app_id):
    """ Return the OAuth credentials for the given app.
    Must be a machine app to perform this call.
    """
    app = _find_app(app_id)
    if app is None:
        raise Http404
    
    json = {
        'consumer_key': app.email,       # Is email really what's used as key?
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
        # we already have the oauth_request in context, so we don't get
        # it again
        app = request.principal
        request_token = OAUTH_SERVER.generate_request_token(
            request.oauth_request,
            record_id=request.POST.get('smart_record_id', None),
            offline_capable=request.POST.get('offline', False)
        )

        return HttpResponse(request_token.to_string(), mimetype='text/plain')
    except oauth.OAuthError, e:
        traceback.print_exc(file=sys.stderr)

    # bad signature (or no signature), unauthorized
    return HttpResponse('Unauthorized', status=401)


def exchange_token(request):
    # ask the oauth server to exchange a request token into an access token
    # this will check proper oauth for this action
    try:
        access_token = OAUTH_SERVER.exchange_request_token(request.oauth_request)
        return HttpResponse(access_token.to_string(), mimetype='text/plain')
    except oauth.OAuthError, e:
        traceback.print_exc(file=sys.stderr)

    # bad signature (or no signature), unauthorized
    return HttpResponse('Unauthorized', status=401)


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
        rt = ReqToken.objects.get(token=request_token)
    except models.ReqToken.DoesNotExist:
        return HttpResponse('Unauthorized', status=401)

    # already claimed by someone other than me?
    if rt.authorized_by is not None and rt.authorized_by != request.principal:
        return HttpResponse('Unauthorized', status=401)

    rt.authorized_by = request.principal
    rt.save()
    return HttpResponse(request.principal.email)


@paramloader()
def request_token_info(request, request_token):
    """
    get info about the request token
    """
    rt = ReqToken.objects.get(token=request_token)
    share = None

    try:
        if rt.record:
            share = Share.objects.get(record=rt.record, with_app=rt.app, authorized_by=request.principal)
    except Share.DoesNotExist:
        pass

    data = {'request_token': rt, 'share': share}
    return render_template('requesttoken', data, type='xml')


@paramloader()
def request_token_approve(request, request_token):
    rt = ReqToken.objects.get(token=request_token)

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
        raise Exception("Must have a record bound to token or a record_id passed in to authorize")

    # no oauth_callback defined? Not a chance
    manifest = simplejson.loads(rt.app.manifest)
    if 'oauth_callback' not in manifest:
        raise Exception("This app does not define an oauth_callback, cannot authorize")

    # get the callback -- must be in the manifest, we do not use the one
    # provided in the request header.
    #callback = request_token.oauth_callback or request_token.app.callback_url
    callback = manifest['oauth_callback']

    record = rt.record
    if not record:
        record = Record.objects.get(id=record_id)

    # authorize the request token and redirect
    request_token = OAUTH_SERVER.authorize_request_token(rt.token, record=record, account=request.principal, offline=offline)
    redirect_url = "%s?oauth_token=%s&oauth_verifier=%s" % (callback, request_token.token, request_token.verifier)

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
    long_lived_token = principal.share.new_access_token(new_token, new_secret, account=None)

    return HttpResponse(long_lived_token.to_string(), mimetype='text/plain')
