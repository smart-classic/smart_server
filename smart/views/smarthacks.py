"""
Quick hacks for SMArt

Ben Adida
"""

from base import *
from smart.lib import utils
from django.db import models, transaction, IntegrityError
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
import psycopg2
import psycopg2.extras
from rdflib import ConjunctiveGraph, Namespace, Literal
from StringIO import StringIO
import smart.models
from smart.models.rdf_store import SesameConnector, DemographicConnector
from pha import immediate_tokens_for_browser_auth
import RDF
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
    return render_template('record_list', {'records': [r for r in Record.objects.all()]}, type='xml')

@paramloader()
def add_app(request, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    AccountApp.objects.create(account = account, app = app)
    return DONE

@paramloader()
def launch_app(request, record, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    sid = transaction.savepoint()
    try:
        AccountApp.objects.create(account = account, app = app)
    except Exception,e:
        if isinstance(e, IntegrityError):
            transaction.savepoint_rollback(sid)

    t = immediate_tokens_for_browser_auth(record, account, app)

    return render_template('token', 
                             {'token':          t, 
                              'app_email':      app.email, 
                              'account_email':  account.email}, 
                            type='xml')



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
    c = DemographicConnector()
    q = request.GET.get('sparql', None)
    res = c.sparql(q)
    
    m = utils.parse_rdf(res)
    d = utils.default_ns()
    print "Got", res
    people = m.find_statements(RDF.Statement(None, d['rdf']['type'], d['foaf']['Person']))
    
    record_list = []
    for p in people:
        record = Record()
        record.id = utils.strip_ns(p.subject, "http://smartplatforms.org/records/")
        record.fn = list(m.find_statements(RDF.Statement(p.subject, d['foaf']['givenName'], None)))[0].object.literal_value['string']
        record.ln = list(m.find_statements(RDF.Statement(p.subject, d['foaf']['familyName'], None)))[0].object.literal_value['string']
        dob = list(m.find_statements(RDF.Statement(p.subject, d['sp']['birthday'], None)))[0].object.literal_value['string']
        record.dob = dob[4:6]+'-'+dob[6:8]+'-'+dob[0:4]
        record_list.append(record)
    print "record list: ", record_list
    return render_template('record_list', {'records': record_list}, type='xml')

def allow_options(request, **kwargs):
    r =  utils.x_domain(HttpResponse())
    r['Access-Control-Allow-Methods'] = "POST, GET, PUT, DELETE"
    r['Access-Control-Allow-Headers'] = "authorization,x-requested-with"
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
