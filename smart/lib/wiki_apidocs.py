# how to run
# from smart_server dir
# (bash) export PYTHONPATH=.:..
# python smart/lib/wiki_apidocs.py payload > payload
# or
# python smart/lib/wiki_apidocs.py api > api

import sys
import copy
stdout = sys.stdout
sys.stdout = sys.stderr
from smart.common.rdf_tools.rdf_ontology import *
from smart.common.rdf_tools.util import bound_graph, URIRef
sys.stdout = stdout

def strip_smart(s):
    return s.replace("http://smartplatforms.org", "")

def type_start(t):
    name = type_name_string(t)
    if (sp.Code in [x.uri for x in t.parents]):
        name += " code"

    description = t.description
    example = t.example
    print "==%s RDF==\n"%name

    if len(t.parents) > 0:
        print "%s is a subtype of and inherits properties from:"%type_name_string(t)
        parents = []
        for p in sorted(t.parents, key=lambda x: type_name_string(x)):
            parents.append("[[#%s RDF| %s]]"%( type_name_string(p),type_name_string(p)))
        print ", ".join(parents)
        print "\n" 
    if description: print "%s"%description+"\n"

    if t.equivalent_classes:
        ec = filter(lambda x: x.one_of, t.equivalent_classes)
        print "''Constrained to one of:'' \n<pre class='code'>"
        for member in [x for c in ec for x in c.one_of]:
            ts  = filter(lambda x: x != owl.NamedIndividual, member.type)
            identifier = split_uri(member.uri)
            system = str(member.uri).split(identifier)[0]
            spcode = split_uri(str(t.uri))
            print """<spcode:%s rdf:about="%s">
    <rdf:type rdf:resource="http://smartplatforms.org/terms#Code" /> 
    <dcterms:title>%s</dcterms:title>
    <sp:system>%s</sp:system>
    <dcterms:identifier>%s</dcterms:identifier> 
</spcode:%s>"""%(spcode, str(member.uri), member.title, system, identifier, spcode)
        print "</pre>"

    if example:
        print "<pre class='code'>%s</pre>\n"%example


def properties_start(type):
    print """{| class='datamodel'
              |+ align="bottom" |''%s Properties''
              |-""" % (type)


def properties_row(property, name,card, description, required_p):
    if required_p:
      print "|width='30%%'|'''%s'''<br /><small>%s</small>\n|width='20%%'|<small>&#91;%s&#93;</small>\n|width='50%%'|%s\n|-"%(property, card, name, description)
    else:
      print "|width='30%%'|%s<br /><small>%s</small>\n|width='20%%'|<small>&#91;%s&#93;</small>\n|width='50%%'|%s\n|-"%(property, card, name, description)

def properties_end():
    print """|}"""

def wiki_batch_start(batch):
    print "\n=%s=\n"%batch

def type_name_string(t):
    if t.name:
        return str(t.name)
    return split_uri(str(t.uri))

def split_uri(t):
    try: 
        return str(t).rsplit("#",1)[1]
    except:
        try: 
            return str(t).rsplit("/",1)[1]
        except: 
            return ""
    
def wiki_payload_for_type(t):
    type_start(t)    
    wiki_properties_for_type(t)

cardinalities  = {"0 - 1": "Optional: 0 or 1", 
                  "0 - Many": "Optional: 0 or more", 
                  "1": "Required: exactly 1", 
                  "1 - Many": "Required: 1 or more"}
    
def wiki_properties_for_type(t):
    if len(t.object_properties) + len(t.data_properties) == 0:
        return
    properties_start(t.uri)
    for c in sorted(t.object_properties + t.data_properties, key=lambda r: str(r.uri)):
        name = type_name_string(c)
        desc = c.description
        m = bound_graph().namespace_manager
        uri = '['+str(t.uri)+' '+m.normalizeUri(t.uri)+']'

        if type(c) is OWL_ObjectProperty:
            is_code = sp.Code in [p.uri for p in c.to_class.parents] and " code" or ""
            targetname = type_name_string(c.to_class)+ is_code

            desc = "[[#%s RDF | %s]]"%(targetname, targetname)
            further = filter(lambda x: isinstance(x.all_values_from, OWL_Restriction), c.restrictions)
            for f in further:
                p = split_uri(str(f.all_values_from.on_property))
                avf = f.all_values_from
                if avf.has_value:
                    desc += "where "+ p +   " has value: %s"%avf.has_value
                else:
                    pc = avf.all_values_from
                    pc = type_name_string(pc)
                    desc += " where "+ p +   " comes from [[#%s code RDF | %s]]"%(pc,pc)

            if c.description:
                desc += "\n\n" + c.description

        elif type(c) is OWL_DataProperty:
            avf = filter(lambda x: x.all_values_from, c.restrictions)
            if len(avf) >0:
              u = avf[0].all_values_from.uri
              d = '&#91;['+str(u)+' '+m.normalizeUri(u)+']&#93;'
            else: d =  '&#91;['+str(rdfs.Literal)+' '+m.normalizeUri(rdfs.Literal)+']&#93;'
            desc += " "+ d
            
        cardinality = cardinalities[c.cardinality_string]
        required_p = False
        if c.cardinality_string[0] == '1':
          required_p = True
          
        properties_row(name, uri, cardinality, desc, required_p)
    properties_end()
    
def wiki_api_for_type(t, calls_for_t):
    print "=== %s ==="%t.name
    print "[[Developers_Documentation:_RDF_Data#%s_RDF | RDF Payload description]]\n"%t.name

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
calls_to_document = copy.copy(api_calls)

for t in api_types:
    if t.is_statement or len(t.calls) > 0:
        main_types.append(t)
    elif (sp.Component in [x.uri for x in t.parents]):
        main_types.append(t)

def type_sort_order(x): 
    if x.is_statement or len(x.calls) > 0:
        is_record = filter(lambda x: "record" in x, [c.category for c in x.calls])
        if len(is_record) > 0 or len(x.calls) == 0:
            return "Clinical Statement"
        return "Container-level"
    elif sp.Code in [p.uri for p in x.parents]:
        return "Data code"
    else:
        return "Component"

def call_category(x):
    return x.category.split("_")[0].capitalize()

def call_sort_order(x):
    
    m = {"GET" : 10, "POST":20,"PUT":30,"DELETE":40}    
    ret =  m[x.method]
    if ("items" in x.category): ret -= 1
    ret = call_category(x) + str(x.target) + str(ret)
    return ret

main_types = sorted(main_types, key=lambda x: type_sort_order(x) + str(x.name))
calls_to_document = sorted(calls_to_document, key=call_sort_order)

import sys
if __name__=="__main__":
    if "payload" in sys.argv:
        current_batch = None
        for t in main_types: 
            if type_sort_order(t) != current_batch:
                current_batch = type_sort_order(t)
                wiki_batch_start(current_batch+" Types") # e.g. "Record Items" or "Container Items"
            wiki_payload_for_type(t)

            
    if "api" in sys.argv:
        current_batch = None
        processed = []
        for t in calls_to_document: 
            if call_category(t) != current_batch:
                current_batch = call_category(t)
                wiki_batch_start(current_batch+" Calls")
            if (t in processed): continue

            target = SMART_Class[t.target]
            calls_for_t = filter(lambda x: call_category(x)==current_batch, sorted(target.calls))
            processed.extend(calls_for_t)
            wiki_api_for_type(target, calls_for_t)
