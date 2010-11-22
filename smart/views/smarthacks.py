"""
Quick hacks for SMArt

Ben Adida
Josh Mandel
"""

from base import *
from smart.lib import utils
from smart.lib.utils import *
from django.http import HttpResponse
from django.conf import settings
from smart.models import *
from smart.models import rdf_ontology 
from pha import immediate_tokens_for_browser_auth
from smart.models.rdf_rest_operations import *
import RDF
import datetime

SAMPLE_NOTIFICATION = {
    'id' : 'foonotification',
    'sender' : {'email':'foo@smart.org'},
    'created_at' : '2010-06-21 13:45',
    'content' : 'a sample notification',
    }

def container_capabilities(request, **kwargs):
    ns = utils.default_ns()
    m = RDF.Model()
    m.append(RDF.Statement(RDF.Node(uri_string=settings.SITE_URL_PREFIX),
             ns['rdf']['type'],
             ns['sp']['container']))

    m.append(RDF.Statement(RDF.Node(uri_string=settings.SITE_URL_PREFIX),
             ns['sp']['capability'],
             ns['sp']['capability/SNOMED/lookup']))
    m.append(RDF.Statement(RDF.Node(uri_string=settings.SITE_URL_PREFIX),
             ns['sp']['capability'],
             ns['sp']['capability/SPL/lookup']))
    m.append(RDF.Statement(RDF.Node(uri_string=settings.SITE_URL_PREFIX),
             ns['sp']['capability'],
             ns['sp']['capability/Pillbox/lookup']))
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))



@paramloader()
def record_list(request, account):
    return render_template('record_list', {'records': [ar.record for ar in account.accountrecord_set.all()]}, type='xml')

@paramloader()
def account_notifications(request, account):
    return render_template('notifications', {'notifications': [SAMPLE_NOTIFICATION]})

def record_by_token(request):
    print "token", request.oauth_request.token
    t = request.oauth_request.token
    r = t.share.record
    return HttpResponse(r.get_demographic_rdf(), mimetype="application/rdf+xml")

@paramloader()
def record_info(request, record):
    return render_template('record', {'record': record})
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

@paramloader()
def launch_app(request, record, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    print "Adding AccountApp"
    AccountApp.objects.get_or_create(account = account, app = app)
    print "Added AccountApp"

    t = immediate_tokens_for_browser_auth(record, account, app)

    return render_template('token', 
                             {'token':          t, 
                              'app_email':      app.email, 
                              'account_email':  account.email}, 
                            type='xml')


def generate_oauth_record_tokens(record, app):
    share, created_p = Share.objects.get_or_create( record   = record, 
                                                               with_app = app,
                                                               defaults = {'authorized_at': datetime.datetime.utcnow()})

    token, secret = oauth.generate_token_and_secret()
        
    ret =  share.new_access_token(token, secret)  
    ret.save()
    
    return ret


@paramloader()
def get_record_tokens(request, record, app):
    return get_record_tokens_helper(record, app)
    
def get_record_tokens_helper(record, app):
    t = generate_oauth_record_tokens(record, app)

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

    # Find the preferred app for this webhook...
    try:
        hook = AppWebHook.objects.filter(name=webhook_name)[0]
    except:
        raise Exception("No hook exists with name:  '%s'"%webhook_name)
    
    data = request.raw_post_data
    if (request.method == 'GET'): data = request.META['QUERY_STRING']    
    
    print "requesting web hook", hook.url, request.method, data    
    response = utils.url_request(hook.url, request.method, {}, data)
    print "GOT,", response
    return utils.x_domain(HttpResponse(response, mimetype='application/rdf+xml'))

def download_ontology(request, **kwargs):
    import os
    f = open(os.path.join(settings.APP_HOME, "smart/document_processing/schema/smart.owl")).read()
    return HttpResponse(f, mimetype="application/rdf+xml")

# hook to build in demographics-specific behavior: 
# if a record doesn't exist, create it before adding
# demographic data
def put_demographics(request, record_id, obj_type, parent_obj_type=None, **kwargs):
  try:
    Record.objects.get(id=record_id)
  except:
    Record.objects.create(id=record_id)
  record_delete_object(request, record_id, obj_type, **kwargs)
  return record_post_objects(request, record_id, obj_type, parent_obj_type, **kwargs)