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

@paramloader()
def record_info(request, record):
    return render_template('record', {'record': record})
@paramloader()
def record_apps(request, record):
    return render_template('phas', {'phas': [ra.app for ra in record.recordapp_set.all()]})


@paramloader()
def record_add_app(request, record, app):
    """
    expecting
    PUT /records/{record_id}/apps/{app_email}
    """
    try:
        RecordApp.objects.create(record = record, app = app)
    except:
        # we assume htis is a duplicate, no problem
        pass

    return DONE

@paramloader()
def record_remove_app(request, record, app):
    """
    expecting
    DELETE /records/{record_id}/apps/{app_email}
    """
    RecordApp.objects.get(record = record, app = app).delete()
    return DONE

@paramloader()
def meds(request, medcall, record):
    fixture = "meds_%s.ccr"%("")
    raw_xml = render_template_raw("fixtures/%s"%fixture, {})
    transformed = utils.xslt_ccr_to_rdf(raw_xml)
   
    g = ConjunctiveGraph()
    g.parse(StringIO(transformed))

    
    rxcui_ids = [r[0].decode().split('/')[-1] 
                 for r in 
                    g.query("""SELECT ?cui_id  
                               WHERE {
                               ?med rdf:type med:medication .
                               ?med med:drug ?cui_id .
                               }""", 
                               initNs=dict(g.namespaces()))]
    for rxcui_id in rxcui_ids:
        print "ADDING", rxcui_id
        rxn_related(rxcui_id=rxcui_id, graph=g)
            
    mimetype = 'application/rdf+xml'
    ret = g.serialize()
    print ret
    return HttpResponse(ret, mimetype=mimetype)


def rxn_related(rxcui_id, graph):
           
   dcterms = Namespace('http://purl.org/rss/1.0/modules/dcterms/', "dctems")
   med = Namespace('http://smartplatforms.org/med#')
   rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
   rxn=Namespace("http://link.informatics.stonybrook.edu/rxnorm/")
   rxcui=Namespace( "http://link.informatics.stonybrook.edu/rxnorm/RXCUI/")
   rxaui=Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXAUI/")
   rxatn=Namespace("http://link.informatics.stonybrook.edu/rxnorm/RXATN#")
   rxrel=Namespace("http://link.informatics.stonybrook.edu/rxnorm/REL#")

   graph.bind("rxn", rxn)
   graph.bind("rxaui", rxaui)
   graph.bind("rxrel", rxrel)
   graph.bind("rxatn", rxatn)
   graph.bind("rxcui", rxcui)
   
   conn=psycopg2.connect("dbname='%s' user='%s' password='%s'"%
                             (settings.DATABASE_RXN, 
                              settings.DATABASE_USER, 
                              settings.DATABASE_PASSWORD))
   
   cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
   cur.execute("""select distinct rxcui, rxaui, atn, atv from 
       rxnsat where rxcui=%s and suppress='N' and 
       atn != 'NDC' order by rxaui, atn;""", (rxcui_id,))
   
   rows = cur.fetchall()
   
   graph.add((rxcui[rxcui_id], rdf['type'], rxcui))
   for row in rows:
       atn = row['atn'].replace(" ", "_")
       graph.add((rxcui['%s'%row['rxcui']], rxn['has_RXAUI'], rxaui[row['rxaui']] ))
       graph.add((rxaui[row['rxaui']], rxatn[atn], Literal(row['atv']) ))

   cur.execute("""select min(rela) as rela, min(str) as str from 
           rxnrel r join rxnconso c on r.rxcui1=c.rxcui 
           where rxcui2=%s group by rela;""", (rxcui_id,))
   
   rows = cur.fetchall()
   for row in rows:
       graph.add((rxcui[rxcui_id], rxrel[row['rela']], Literal(row['str']) ))

   return