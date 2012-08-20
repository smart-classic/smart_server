from smart.lib import utils
from smart.common.rdf_tools.util import parse_rdf, NS
from rdflib import Graph, ConjunctiveGraph, Namespace, BNode, Literal, RDF, URIRef
from rdflib.collection import Collection
from django.conf import settings
import urllib, uuid, base64, time
import time, json, sys