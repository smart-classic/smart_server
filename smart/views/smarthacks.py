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
def account_add_app(request, account, app):
    """
    expecting
    PUT /records/{record_id}/apps/{app_email}
    """
    try:
        AccountApp.objects.create(account = account, app = app)
    except:
        # we assume htis is a duplicate, no problem
        pass

#    newaccess = immediate_tokens_for_browser_auth(record, app)
#    print "***************** GENERATED NEWACCESS", newaccess


    return DONE

@paramloader()
def account_remove_app(request, account, app):
    """
    expecting
    DELETE /records/{record_id}/apps/{app_email}
    """
    AccountApp.objects.get(account = account, app = app).delete()
    return DONE

def record_search(request):
    fname = request.GET.get('fname', None)
    lname = request.GET.get('lname', None)
    dob = request.GET.get('dob', None)
    zip = request.GET.get('zip', None)
    sex = request.GET.get('sex', None)
    
    print "Searching for ", fname, lname, dob ,zip, sex
    print render_template('record_list', {'records': [r for r in Record.objects.all()]}, type='xml')

    return render_template('record_list', {'records': [r for r in Record.objects.all()]}, type='xml')

#@paramloader()
#
#def meds(request, medcall, record):
#    return utils.get_rdf_meds()
#    fixture = "meds_%s.ccr"%("")
#    raw_xml = render_template_raw("fixtures/%s"%fixture, {})
#    rdf_xml = utils.meds_as_rdf(raw_xml)
#    print "rdf version ", rdf_xml
#    return HttpResponse(rdf_xml, mimetype="application/rdf+xml")
