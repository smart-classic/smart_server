from smart.models.rdf_ontology import *

def strip_smart(s):
    return s.replace("http://smartplatforms.org", "")

def type_start(name, description, example):
    print "==%s RDF==\n"%name
    print description+"\n"
    if (example != ""):
        print "<pre>%s</pre>\n"%example


def properties_start(type):
    print """'''%s Predicates'''\n{| border="1" cellpadding="20" cellspacing="0"
|+ align="bottom" style="color:#e76700;" |''%s Predicates''
|-""" % (type, type)

def properties_row(property, name, description):
    print "|%s\n|%s\n|%s\n|-"%(property,name, description)

def properties_end():
    print """|}"""

def wiki_batch_start(batch):
    print "\n=%s=\n"%batch

def wiki_payload_for_type(t):
    type_start(t.name, t.description, t.example)    
    wiki_properties_for_type(t)
    
types_covered = []    
def wiki_properties_for_type(t, label=None):
    if t in types_covered: return
    types_covered.append(t)
    
    if label == None: label = t.type
    
    if len(t.children.values() + t.properties) == 0:
        return
    
    properties_start(label)
    name="nopropertyname"
    desc="nopropertydesc"
    
    child_types_pending = {}    
    for c, ctype in t.children.iteritems():
        try:
            name, desc = t.property_description(c)
        except: 
            pass
        properties_row(c, name, desc)
        
        try:
            child_types_pending[c] = api_types[ctype]
        except: print "CHLID failed for ", ctype
    
    for p in t.properties:
        try:
                name, desc = t.property_description(p)
        except: pass
        properties_row(p, name, desc)

    properties_end()

    for c, ctype in child_types_pending.iteritems():
        print "\n"
        wiki_properties_for_type(ctype, label=c)

    
def wiki_api_for_type(t):
    print "=== %s ==="%t.name
    print "[[Developers_Documentation:_RDF_Data#%s_RDF | RDF Payload description]]"%t.name, "\n"
    calls_for_t = filter(lambda c: c.target == t.type, api_calls)
    calls_for_t = sorted(calls_for_t, key=lambda x: x.sort_order)

    last_description = ""
    for call in calls_for_t:
        if (call.description != last_description):
            print "\n\n",call.description
        last_description = call.description
        print " ", strip_smart(call.method), call.path
        
        
             
ts = []
for t in api_types.values():
    try: 
        assert len(t.name) >0, "Expect types to have a name."
        ts.append(t)
    except: pass    
ts = sorted(ts, key=lambda x: x.sort_order + x.name)

import sys
if __name__=="__main__":
    if "payload" in sys.argv:
        current_batch = None
        for t in ts: 
            if t.sort_order != current_batch:
                current_batch = t.sort_order
                wiki_batch_start(current_batch+" Types")
            wiki_payload_for_type(t)
            
    if "api" in sys.argv:
        current_batch = None
        for t in ts: 
            if t.sort_order != current_batch:
                current_batch = t.sort_order
                wiki_batch_start(current_batch+" Calls")
            wiki_api_for_type(t)