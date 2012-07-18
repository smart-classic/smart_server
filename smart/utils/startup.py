import os
import sys
from django.conf import settings
from smart_server.smart.models.apps import OAuthApp
from smart_server.smart.triplestore.triplestore import TripleStore

def check_environment():
    check_database()
    check_triplestore()

def check_database():
    # ensure database is online + accessible
    try:
        a = OAuthApp.objects.all()
    except:
        assert False, "Could not connect to database.  Check settings."

def check_triplestore():
    # ensure triplestore is online + accessible
    try:
        c = TripleStore()
        r = c.sparql("""CONSTRUCT {<urn:test> a <urn:value>} where {<urn:test> a <urn:value>}""")
    except:
        assert False, "Could not connect to triplestore.  Check settings."    
