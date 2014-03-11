# -*- coding: utf-8 -*-
"""
The RDFExtras namespace package.
"""

__author__ = "Niklas Lindström"
__version__ = "0.3-dev"

# This is a namespace package.
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    import pkgutil
    __path__ = pkgutil.extend_path(__path__, __name__)


import logging

class NullHandler(logging.Handler):
    """
    c.f.
    http://docs.python.org/howto/logging.html#library-config
    and
    http://docs.python.org/release/3.1.3/library/logging.\
    html#configuring-logging-for-a-library
    """
    def emit(self, record):
        pass

hndlr = NullHandler()
logging.getLogger("rdfextras").addHandler(hndlr)

def registerplugins():
    """
    If rdfextras is installed with setuptools, all plugins are registered
    through entry_points. This is strongly recommended. 

    If only distutils is available, the plugins must be registed manually
    This method will register all rdfextras plugins

    """
    from rdflib import plugin
    from rdflib.query import Processor

    try:
        x=plugin.get('sparql',Processor)
        return # plugins already registered
    except:
        pass # must register plugins    

    from rdflib.store import Store
    from rdflib.parser import Parser
    from rdflib.serializer import Serializer
    from rdflib.query import ResultParser, ResultSerializer, Result

    plugin.register('rdf-json', Parser,
        'rdfextras.parsers.rdfjson', 'RdfJsonParser')
    plugin.register('json-ld', Parser,
        'rdfextras.parsers.jsonld', 'JsonLDParser')
    plugin.register('rdf-json', Serializer,
        'rdfextras.serializers.rdfjson', 'RdfJsonSerializer')
    plugin.register('json-ld', Serializer,
        'rdfextras.serializers.jsonld', 'JsonLDSerializer')
    plugin.register('html', Serializer,
        'rdfextras.sparql.results.htmlresults', 'HTMLSerializer')

    plugin.register('sparql', Result,
        'rdfextras.sparql.query', 'SPARQLQueryResult')
    plugin.register('sparql', Processor,
        'rdfextras.sparql.processor', 'Processor')

    plugin.register('html', ResultSerializer,
        'rdfextras.sparql.results.htmlresults', 'HTMLResultSerializer')
    plugin.register('xml', ResultSerializer,
        'rdfextras.sparql.results.xmlresults', 'XMLResultSerializer')
    plugin.register('json', ResultSerializer,
        'rdfextras.sparql.results.jsonresults', 'JSONResultSerializer')
    plugin.register('xml', ResultParser,
        'rdfextras.sparql.results.xmlresults', 'XMLResultParser')
    plugin.register('json', ResultParser,
        'rdfextras.sparql.results.jsonresults', 'JSONResultParser')

    plugin.register('SPARQL', Store,
        'rdfextras.store.SPARQL', 'SPARQLStore')
