from smart.models.rdf_ontology import *

def strip_smart(s):
    return s.replace("http://smartplatforms.org", "")

def type_start(name, description, example):
    print "==%s RDF==\n"%name
    if description: print description+"\n"
    if (example and example != ""):
        print "<pre>%s</pre>\n"%example


def properties_start(type):
    print """'''%s Direct Properties'''\n{| border="1" cellpadding="20" cellspacing="0"
|+ align="bottom" style="color:#e76700;" |''%s Predicates''
|-""" % (type, type)

def children_start(type):
    print """'''%s Child Properties '''\n{| border="1" cellpadding="20" cellspacing="0"
|+ align="bottom" style="color:#e76700;" |''%s Predicates''
|-""" % (type, type)


def properties_row(property, name, description):
    print "|%s\n|%s\n|%s\n|-"%(property,name, description)

def properties_end():
    print """|}"""

def wiki_batch_start(batch):
    print "\n=%s=\n"%batch

def wiki_payload_for_type(t):
    type_start(t.name and t.name or t.type.rsplit("#")[1], t.description, t.example)    
    wiki_properties_for_type(t)
    
types_covered = []    
def wiki_properties_for_type(t, label=None):
    if t in types_covered: return
    types_covered.append(t)
    
    if label == None: label = t.type
    
    if len(t.children.values() + t.properties) == 0:
        return
    
    name="nopropertyname"
    desc="nopropertydesc"
 
    
    children = sorted(t.children.keys())
    if len(children) > 0:
       children_start(label)       
        
    for c in children:
        try:
            name, desc = t.property_description(c)
        except: 
            pass
        properties_row(c, name, desc)
    if len(children) > 0:
       properties_end()       
 
    if len(t.properties) > 0:
       properties_start(label)       
    for p in sorted(t.properties):
        try:
                name, desc = t.property_description(p)
        except: pass
        properties_row(p, name, desc)
    if len(t.properties) > 0:
        properties_end()



    
def wiki_api_for_type(t):
    print "=== %s ==="%t.name
    print "[[Developers_Documentation:_RDF_Data#%s_RDF | RDF Payload description]]\n"%t.name
    calls_for_t = filter(lambda c: c.target == t.type, api_calls)
    calls_for_t = sorted(calls_for_t, key=lambda x: x.sort_order)

    last_description = ""
    for call in calls_for_t:
        if (call.method != "GET"): continue # Document only the GET calls for now!
        if (call.description != last_description):
            print call.description
        
        print " ", strip_smart(call.method), call.path
        
        if (call.description != last_description):
            print ""
            last_description = call.description
        
        
             
main_types = []
helper_types = []
for t in api_types.values():
    if (t.path == None):
        helper_types.append(t)
    else:
        main_types.append(t)

main_types = sorted(main_types, key=lambda x: x.sort_order + x.name)
helper_types = sorted(helper_types, key=lambda x: x.type)

import sys
if __name__=="__main__":
    if "payload" in sys.argv:
        current_batch = None
        for t in main_types: 
            if t.sort_order != current_batch:
                current_batch = t.sort_order
                wiki_batch_start(current_batch+" Types") # e.g. "Record Items" or "Container Items"
            wiki_payload_for_type(t)

        wiki_batch_start("Core Data Types") # e.g. "Record Items" or "Container Items"            
        for t in helper_types: 
            wiki_payload_for_type(t)
            
            
            
    if "api" in sys.argv:
        current_batch = None
        for t in main_types: 
            if t.sort_order != current_batch:
                current_batch = t.sort_order
                wiki_batch_start(current_batch+" Calls")
            wiki_api_for_type(t)