"""
Quick hacks for SMArt

Ben Adida
"""

from base import *
from smart.lib import utils
from django.http import HttpResponseBadRequest
from django.conf import settings
import psycopg2
import psycopg2.extras
from rdflib import ConjunctiveGraph, Namespace, Literal
from StringIO import StringIO
import smart.models
from pha import immediate_tokens_for_browser_auth
import RDF


SAMPLE_NOTIFICATION = {
    'id' : 'foonotification',
    'sender' : {'email':'foo@smart.org'},
    'created_at' : '2010-06-21 13:45',
    'content' : 'a sample notification',
    }

@paramloader()
def record_list(request, account):
    return render_template('record_list', {'records': [ar.record for ar in account.accountrecord_set.all()]}, type='xml')

@paramloader()
def account_notifications(request, account):
    return render_template('notifications', {'notifications': [SAMPLE_NOTIFICATION]})

def record_by_token(request):
    print "token", request.oauth_request.token
    t = request.oauth_request.token
    return render_template('record', {'record': t.share.record})

@paramloader()
def record_info(request, record):
    return render_template('record', {'record': record})
@paramloader()
def record_apps(request, record):
    return render_template('phas', {'phas': [ra.app for ra in record.recordapp_set.order_by("app__name")]})


@paramloader()
def account_recent_records(request, account):
    return render_template('record_list', {'records': [r for r in Record.objects.all()]}, type='xml')

@paramloader()
def add_app(request, record, account, app):
    """
    expecting
    PUT /accounts/{account_id}/apps/{app_email}
    """
    try:
        AccountApp.objects.create(account = account, app = app)
    except:
        pass

    t = immediate_tokens_for_browser_auth(account, app)

    return render_template('token', 
                             {'token':          t, 
                              'app_email':      app.email, 
                              'account_email':  account.email}, 
                            type='xml')


@paramloader()
def remove_app(request, record, account, app):
    """
    expecting
    DELETE /records/{record_id}/apps/{app_email}
    """
    AccountApp.objects.get(account = account, app = app).delete()
    return DONE

def record_search(request):
    
    db = settings.DATABASE_REDLAND                                                                                                                                                              
    u = settings.DATABASE_USER                                                                                           
    p =settings.DATABASE_PASSWORD
    rs = RDF.Storage(storage_name="postgresql", name=db,
                    options_string="new='no',database='%s',host='localhost',user='%s',password='%s',contexts='yes'"%
                    (db, u, p))      
    
    model = RDF.Model(storage=rs)

    # todo: sanitize these before passing them in to librdf -JM

    sparql = request.GET.get('sparql', None)     
    print "Searching for ", sparql


    record_list = []    
    for r in RDF.SPARQLQuery(sparql.encode()).execute(model):
        print "matching", r
        record_id = utils.strip_ns(r['person'], "http://smartplatforms.org/records/")        
        print "matching", record_id
        record_list.append(Record.objects.get(id=record_id))
    
    return render_template('record_list', {'records': record_list}, type='xml')

#@paramloader()
#
#def meds(request, medcall, record):
#    return utils.get_rdf_meds()
#    fixture = "meds_%s.ccr"%("")
#    raw_xml = render_template_raw("fixtures/%s"%fixture, {})
#    rdf_xml = utils.meds_as_rdf(raw_xml)
#    print "rdf version ", rdf_xml
#    return HttpResponse(rdf_xml, mimetype="application/rdf+xml")
