"""
Quick hacks for SMArt

Ben Adida
Josh Mandel
"""

from base import *
from smart.lib import utils
from smart.lib.utils import *
from smart.common.util import rdf, sp, bound_graph, URIRef, Namespace
from django.http import HttpResponse
from django.conf import settings
from smart.models import *
from smart.models.record_object import RecordObject
from smart.models.rdf_rest_operations import *
from oauth.oauth import OAuthRequest
from smart.models.ontology_url_patterns import CallMapper
import datetime

SAMPLE_NOTIFICATION = {
    'id' : 'foonotification',
    'sender' : {'email':'foo@smart.org'},
    'created_at' : '2010-06-21 13:45',
    'content' : 'a sample notification',
    }

sporg = Namespace("http://smartplatforms.org/")


@CallMapper.register(method="GET",
                     category="container_items",
                     target="http://smartplatforms.org/terms#Container")
def container_capabilities(request, **kwargs):
    m = bound_graph()
    site = URIRef(settings.SITE_URL_PREFIX)
    print "avail", dir(m)
    m.add((site, rdf['type'], sp['Container']))

    m.add((site, sp['capability'], sporg['capability/SNOMED/lookup']))

    m.add((site, sp['capability'], sporg['capability/SPL/lookup']))

    m.add((site,
             sp['capability'],
             sporg['capability/Pillbox/lookup']))
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))

@paramloader()
def record_list(request, account):
    return render_template('record_list', {'records': [ar.record for ar in account.accountrecord_set.all()]}, type='xml')

def record_by_token(request):
    print "token", request.oauth_request.token
    t = request.oauth_request.token
    r = t.share.record
    return HttpResponse(r.get_demographic_rdf(), mimetype="application/rdf+xml")

@paramloader()
def record_info(request, record):
    q = record.query()
    l = Record.search_records(q)
    return render_template('record_list', {'records': l}, type='xml')

@paramloader()
def apps_for_account(request, account):
    return render_template('phas', {'phas': [aa.app for aa in account.accountapp_set.order_by("app__name")]})

@paramloader()
def account_recent_records(request, account):
    return render_template('record_list', {'records': []}, type='xml')

@paramloader()
def add_app(request, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    app = PHA.objects.get(id=app.id)
    AccountApp.objects.create(account = account, app = app)
    return DONE

def immediate_tokens_for_browser_auth(record, account, app, smart_connect_p = True):
    ret = OAUTH_SERVER.generate_and_preauthorize_access_token(app, record=record, account=account)
    ret.smart_connect_p = smart_connect_p
    ret.save()
    return ret
  
def cookie_for_token(t):
    app=t.share.with_app
    try:
        activity = AppActivity.objects.get(name="main", app=app)
    except AppActivity.DoesNotExist:    
        activity = AppActivity.objects.get(app=app)
        
    app_index_req = utils.url_request_build(activity.url, "GET", {}, "")
    oauth_request = OAuthRequest(app, None, app_index_req, oauth_parameters=t.passalong_params)
    oauth_request.sign()
    auth = oauth_request.to_header()["Authorization"]
    return {'oauth_cookie' : auth}

@paramloader()
def launch_app(request, record, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    print "Adding AccountApp"
    AccountApp.objects.get_or_create(account = account, app = app)
    print "Added AccountApp"

    ct = immediate_tokens_for_browser_auth(record, account, app)

    rt = immediate_tokens_for_browser_auth(record, account, app, False)
    cookie = cookie_for_token(rt)

    return render_template('token', 
                             {'connect_token':          ct,
                              'rest_token':          rt, 
                              'api_base':       settings.SITE_URL_PREFIX,
                              'app_email':      app.email, 
                              'account_email':  account.email,
                              'oauth_cookie': cookie}, 
                            type='xml')


def create_proxied_record(request):
    record_id = request.POST['record_id']
    record_name = request.POST['record_name']

    print "ASKED to create proxied record: ", record_id, record_name

    r, created = Record.objects.get_or_create(id=record_id, defaults={'full_name':record_name})
    print "GOT: ", r, created
    if not created and r.full_name != record_name:
        r.full_name = record_name
        r.save()

    return DONE

@paramloader()
def get_record_tokens(request, record, app):
    return get_record_tokens_helper(record, app)
    
def get_record_tokens_helper(record, app):
    t = HELPER_APP_SERVER.generate_and_preauthorize_access_token(app, record=record)
    r  = {'oauth_token' : t.token, 'oauth_token_secret': t.secret, 'smart_record_id' : record.id}
    return utils.x_domain(HttpResponse(urllib.urlencode(r), "application/x-www-form-urlencoded"))
 
@paramloader()
def get_first_record_tokens(request, app):
    record = Record.objects.order_by("id")[0]
    return get_record_tokens_helper(record, app)

@paramloader()
def get_next_record_tokens(request,record, app):
    try:
        record = Record.objects.order_by("id").filter(id__gt=record.id)[0]
        return get_record_tokens_helper(record, app)
    except: raise Http404

@paramloader()
def remove_app(request, account, app):
    """
    expecting
    DELETE /records/{record_id}/apps/{app_email}
    """
    AccountApp.objects.get(account = account, app = app).delete()

    #TODO:  This would be a good hook for removing shares and tokens for this app/account. -JCM
    # pseudocode like;
    # foreach share(account, app):
    #    foreach token(share):
    #         delete token
    #    delete share

    return DONE

def record_search(request):
    q = request.GET.get('sparql', None)
    print "Query for pts", q
    record_list = Record.search_records(q)
    return render_template('record_list', {'records': record_list}, type='xml')

def allow_options(request, **kwargs):
    r =  utils.x_domain(HttpResponse())
    r['Access-Control-Allow-Methods'] = "POST, GET, PUT, DELETE"
    r['Access-Control-Allow-Headers'] = "authorization,x-requested-with,content-type"
    r['Access-Control-Max-Age'] = 60
    print r._headers
    return r

def do_webhook(request, webhook_name):
    hook = None
    headers = {}
    
    # Find the preferred app for this webhook...
    try:
        hook = AppWebHook.objects.filter(name=webhook_name)[0]
    except:
        raise Exception("No hook exists with name:  '%s'"%webhook_name)
    
    data = request.raw_post_data
    if (request.method == 'GET'): data = request.META['QUERY_STRING']    
    
    print "requesting web hook", hook.url, request.method, data

    hook_req = utils.url_request_build(hook.url, request.method, headers, data)
    
    # If the web hook needs patient context, we've got to generate + pass along tokens
    if (hook.requires_patient_context):        
        app = hook.app
        record = request.principal.share.record
        account = request.principal.share.authorized_by
        # Create a new token for the webhook to access the in-context patient record
        token = HELPER_APP_SERVER.generate_and_preauthorize_access_token(app, record=record, account=account)
        
        # And supply the token details as part of the Authorization header, 2-legged signed
        # Using the helper app's consumer token + secret
        # (the 2nd parameter =None --> 2-legged OAuth request)
        oauth_request = OAuthRequest(app, None, hook_req, oauth_parameters=token.passalong_params)
        oauth_request.sign()        
        for (hname, hval) in oauth_request.to_header().iteritems():
            hook_req.headers[hname] = hval 
    
    response = utils.url_request(hook.url, request.method, headers, data)
    print "GOT,", response
    return utils.x_domain(HttpResponse(response, mimetype='application/rdf+xml'))

@CallMapper.register(method="GET",
                     category="container_item",
                     target="http://smartplatforms.org/terms#Ontology")
def download_ontology(request, **kwargs):
    import os
    f = open(os.path.join(settings.APP_HOME, "smart/document_processing/schema/smart.owl")).read()
    return HttpResponse(f, mimetype="application/rdf+xml")

# hook to build in demographics-specific behavior: 
# if a record doesn't exist, create it before adding
# demographic data
@CallMapper.register(method="PUT",
                     category="record_items",
                     target="http://xmlns.com/foaf/0.1/Person")
def put_demographics(request, record_id, obj, **kwargs):
  try:
    Record.objects.get(id=record_id)
  except:
    Record.objects.create(id=record_id)
  record_delete_object(request, record_id, obj, **kwargs)
  return record_post_objects(request, record_id, obj, **kwargs)


def debug_oauth(request, **kwargs):
    from smart.accesscontrol.oauth_servers import OAUTH_SERVER
    ret = "Details of your request: \n\n"

    ret += "Method: %s\n"%request.method
    ret += "URL: %s\n"%request.build_absolute_uri()

    ret += "Headers:\n"
    for k,v in request.META.iteritems():
        if k.startswith("HTTP"):
                ret += "%s: %s"%(k,v)

    ret += "\n"

    try:
      oauth_request = OAUTH_SERVER.extract_oauth_request(djangoutils.extract_request(request))
      ret += "OAuth Debugging: \n\n"
      ret += "SBS: \n"
      sbs = oauth_request.get_signature_base_string()
      ret += sbs
      ret += "Expected Signature: \n"
      ret += oauth.SIGNATURE_METHODS['HMAC-SHA1'].sign(sbs, oauth_request.consumer, oauth_request.token)
      ret += "Your Signature: \n"
      ret += oauth_request.signature
    except oauth.OAuthError as e:
      import traceback
      ret += "An error occurred:\n"
      ret += traceback.format_exc()
    return HttpResponse(ret, "text/plain")

