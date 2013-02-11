from smart.triplestore import *
from smart.models.records import *
from smart.lib.utils import *
from smart.common.rdf_tools.util import URIRef, bound_graph, sp
from string import Template
import re


def record_get_object(request, record_id, obj, **kwargs):
    c = RecordTripleStore(Record.objects.get(id=record_id))
    item_id = URIRef(smart_path(request.path))
    return rdf_response(c.get_objects(request.path, request.GET, obj, [item_id]))


def record_delete_object(request, record_id, obj, **kwargs):
    c = RecordTripleStore(Record.objects.get(id=record_id))
    id = smart_path(request.path)
    return rdf_delete(c, get_statements_by_context(bindings=["<%s>" % id.encode()]))


def record_get_all_objects(request, record_id, obj, **kwargs):
    c = RecordTripleStore(Record.objects.get(id=record_id))
    return rdf_response(c.get_objects(request.path, request.GET, obj))


def record_delete_all_objects(request, record_id, obj, **kwargs):
    c = RecordTripleStore(Record.objects.get(id=record_id))
    return rdf_delete(c, obj.query(patient=c.patient))


def record_post_objects(request, record_id, obj, **kwargs):
    c = RecordTripleStore(Record.objects.get(id=record_id))
    path = smart_path(request.path)
    data = parse_rdf(request.raw_post_data)
    var_bindings = obj.path_var_bindings(path)

    if "record_id" in var_bindings:
        assert var_bindings['record_id'] == record_id, "Mismatched: %s vs. %s" % (record_id, var_bindings['record_id'])
    else:
        var_bindings['record_id'] = record_id

    # Note: no return value! alters data in-place
    obj.prepare_graph(data, None, var_bindings)

    # now data's statements should have generated UUID-based subject URIs
    # but the top-level context URI is still a random bnode
    # print "Default context", len(data.default_context)

    record_node = list(data.triples((None, rdf.type, sp.MedicalRecord)))
    assert len(record_node) == 1, "Found statements about >1 patient in file: %s" % record_node
    record_node = record_node[0][0]

    obj.segregate_nodes(data, record_node)
    data.remove_context(data.default_context)

    #print 'graph: ' + str(data)

    return rdf_post(c, data)

def record_put_object(request, record_id, obj, **kwargs):
    # An idempotent PUT requires:
    #  1.  Ensure we're only putting *one* object
    #  2.  Add its external_id as an attribute in the RDF graph
    #  3.  Add any parent-child links if needed
    #  4.  Delete the thing from existing store, if it's present
    #  5.  POST the (new) thing to the store
    pass
