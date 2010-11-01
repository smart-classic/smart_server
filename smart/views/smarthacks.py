"""
Quick hacks for SMArt

Ben Adida
"""

from base import *
from smart.lib import utils
from smart.lib.utils import smart_base
from django.db import models, transaction, IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest,\
    HttpResponseNotFound
from django.conf import settings
import psycopg2
import psycopg2.extras
from rdflib import ConjunctiveGraph, Namespace, Literal
from StringIO import StringIO
import smart.models
from smart.models.rdf_store import SesameConnector, DemographicConnector
from pha import immediate_tokens_for_browser_auth
import RDF, re
import libxml2


SAMPLE_NOTIFICATION = {
    'id' : 'foonotification',
    'sender' : {'email':'foo@smart.org'},
    'created_at' : '2010-06-21 13:45',
    'content' : 'a sample notification',
    }

def container_capabilities(request):
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
    share, created_p = smart.models.Share.objects.get_or_create( record        = record, 
                                                          with_app      = app,
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
    
    response = utils.url_request(hook.url, request.method, {}, data)
    print "GOT,", response
    return utils.x_domain(HttpResponse(response, mimetype='application/rdf+xml'))


def user_get(request, user_id):
    
    ns = utils.default_ns()
    m = RDF.Model()
    try:
        a = Account.objects.get(id=user_id)
        n = RDF.Node(uri_string="%s/users/%s" % (smart_base, a.id.encode()))
        m.append(RDF.Statement(n, ns['rdf']['type'], ns['sp']['user']))    
        m.append(RDF.Statement(n, ns['dcterms']['title'], RDF.Node(literal=a.full_name.encode())))    
        m.append(RDF.Statement(n, ns['foaf']['mbox'], RDF.Node(literal="mailto:%s"%a.email.encode())))    
    except: return HttpResponseNotFound()
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))

def user_search(request):
    aa = Account.objects.all()

    ns = utils.default_ns()
    m = RDF.Model()
    
    regex  = request.GET.get("regex", None)
    if (regex != None): regex = re.compile(request.GET["regex"])
    
    for a in aa:
        if (regex and not regex.match(a.full_name)): continue
        n = RDF.Node(uri_string="%s/users/%s" % (smart_base, a.email.encode()))
        m.append(RDF.Statement(n, ns['rdf']['type'], ns['sp']['user']))    
        m.append(RDF.Statement(n, ns['dcterms']['title'], RDF.Node(literal=a.full_name.encode())))    
        m.append(RDF.Statement(n, ns['foaf']['mbox'], RDF.Node(literal="mailto:%s"%a.email.encode())))    
        
    
    return utils.x_domain(HttpResponse(utils.serialize_rdf(m), "application/rdf+xml"))

    