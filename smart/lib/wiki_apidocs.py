import sys
stdout = sys.stdout
sys.stdout = sys.stderr
from smart.client.common.rdf_ontology import *
sys.stdout = stdout

def strip_smart(s):
    return s.replace("http://smartplatforms.org", "")

def type_start(t):
    name = type_name_string(t)
    description = t.description
    example = t.example
    print "==%s RDF==\n"%name

    if len(t.parent_classes) > 0:
        print "%s is a subtype of and inherits properties from:"%type_name_string(t)
        parents = []
        for p in t.parent_classes:
            parents.append("[[#%s RDF| %s]] "%( type_name_string(p),type_name_string(p)))
        print ", ".join(parents)
        print "\n" 
    if description: print "%s"%description+"\n"
    if example:
        print "<pre>%s</pre>\n"%example


def properties_start(type):
    print """'''%s Properties'''\n{| border="1" cellpadding="20" cellspacing="0"
|+ align="bottom" style="color:#e76700;" |''%s Properties''
|-""" % (type, type)


def properties_row(property, name,card, description):
    card = "{{nobr|" + card + "}}"
    print "|%s\n|%s\n|%s\n|%s\n|-"%(property,name, card,description)

def properties_end():
    print """|}"""

def wiki_batch_start(batch):
    print "\n=%s=\n"%batch

def type_name_string(t):
    if t.name:
        return str(t.name)

    try: return str(t.uri).rsplit("#",1)[1]
    except:
        try: 
            return str(t.uri).rsplit("/",1)[1]
        except: 
            return ""
    
def wiki_payload_for_type(t):
    type_start(t)    
    wiki_properties_for_type(t)
    
def wiki_properties_for_type(t):
    if len(t.object_properties) + len(t.data_properties) == 0:
        return

    properties_start(t.uri)
    for c in sorted(t.object_properties + t.data_properties, key=lambda r: str(r.uri)):
        name = type_name_string(c)
        desc = c.description

        if type(c) is OWL_ObjectProperty:
            d = (c.to_class.description or "")
            if len(d) > 1000:
                d = d[:1000]+"..."
            if len(d) > 0:
                d = ": " + d

            desc += type_name_string(c.to_class) + " " +d + " [[#%s RDF | (details...)]]"%(type_name_string(c.to_class))
        elif type(c) is OWL_DataProperty:
            desc += (c.all_values_from and c.all_values_from.n3() or "string literal")
        
        properties_row(name, c.uri.n3(), c.cardinality_string, desc)
    properties_end()
    
def wiki_api_for_type(t):
    print "=== %s ==="%t.name
    print "[[Developers_Documentation:_RDF_Data#%s_RDF | RDF Payload description]]\n"%t.name
    calls_for_t = sorted(t.calls)

    last_description = ""
    for call in calls_for_t:
        if (str(call.method) != "GET"): continue # Document only the GET calls for now!
        if (str(call.description) != last_description):
            print str(call.description)
        
        print " ", strip_smart(str(call.method)), str(call.path)
        
        if (str(call.description) != last_description):
            print ""
            last_description = str(call.description)
             

main_types = []
helper_types = []
for t in api_types:
    if (t.is_statement and len(t.calls) > 0):
        main_types.append(t)
    else:
        helper_types.append(t)


def type_sort_order(x): 
    return str(x.calls[0].category).split("_")[0].capitalize()

def call_sort_order(x):
    m = {"GET" : 10, "POST":20,"PUT":30,"DELETE":40}    
    ret =  m[x.method]
    if ("items" in x.category): ret -= 1
    return ret

main_types = sorted(main_types, key=lambda x: type_sort_order(x) + str(x.name))
helper_types = sorted(helper_types, key=lambda x: str(x.uri))

import sys
if __name__=="__main__":
    if "payload" in sys.argv:
        current_batch = None
        for t in main_types: 
            if type_sort_order(t) != current_batch:
                current_batch = type_sort_order(t)
                wiki_batch_start(current_batch+" Types") # e.g. "Record Items" or "Container Items"
            wiki_payload_for_type(t)

        wiki_batch_start("Core Data Types") # e.g. "Record Items" or "Container Items"            
        for t in helper_types: 
            wiki_payload_for_type(t)            
            
            
    if "api" in sys.argv:
        current_batch = None
        for t in main_types: 
            if type_sort_order(t) != current_batch:
                current_batch = type_sort_order(t)
                wiki_batch_start(current_batch+" Calls")
            wiki_api_for_type(t)
