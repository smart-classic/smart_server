"""
Hashing-based RDF update
Josh Mandel

This class helps merge new RDF updates with an existing RDF store.
In particular, it takes an RDF graph and maps every "important" blank node
(i.e. every blank node that has an rdf:type property) and maps it to a Uri 
node. To accomplish this, each subclass of HashedRDFUpdate take responsibility
for objects of a single rdf:type.  The subclass determines which (if any)
existing object a blank node maps to, via the identifying_hash function -- 
and if no suitable object exists, one is created on-the-fly.  The subclass
then passes control recursively to its child_classes, and in this fashion
ever blank node is properly mapped, yielding a "fully labeled" graph.

To use HashedRDFUpdate on an RDF graph, you must know ahead of time what
type of object the graph represents at the root level of the hierarchy.
For example if I have an RDF graph 'g' of med:medications (each of which
contains several sp:fulfillments) for a patient with record 'r',
I would call:

    HashedMedication.conditional_create(model=g,context=r.record_id)
    
At this point g contains no more important blank nodes.  I can then insert
statements from g into a permanent triple store 'pstore' by:

   for s in g:
     if not pstore.contains_statement(s):
        pstore.append(s)
"""

from base import *
from django.utils import simplejson
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from django.conf import settings
from smart.models.records import Record
from string import Template
import hashlib
import RDF

class HashedRDFUpdate(Object):
    Meta = BaseMeta()
    identifying_hash = models.CharField(max_length = 100, null=True)
    uri_string = models.CharField(max_length=200, null=True)
    data = models.TextField(null= False)
    
    
    def __unicode__(self):
      return 'HashedRDFUpdate:   id=%s, identifying_hash=%s' % (
              self.id, 
              self.identifying_hash)
    
    @classmethod
    def conditional_create(cls, model,context=None):
#        print "Conditionally creating ", cls.type, " with context ", context
        for blank_node in cls.get_unmapped_elements(parent=context, model=model):      
            
            id_hash = cls.get_identifying_hash(element=blank_node, parent=context, model=model)
            uri_string = "%s/%s"%(cls.type, id_hash)
            cls.remap_blank_node(model, blank_node.blank_identifier, uri_string)

            for child_class in cls.child_classes:
                child_class.conditional_create(context=RDF.Node(uri_string=uri_string), 
                                               model=model)

    @classmethod 
    def remap_blank_node(cls, model, blank_string, uri_string):
        uri_node = RDF.Node(uri_string=uri_string)
        blank_node = RDF.Node(blank=blank_string)
        for s in model.find_statements(RDF.Statement(blank_node, None, None)):
            del model[s]
            model.append(RDF.Statement(uri_node, s.predicate, s.object))
        for s in model.find_statements(RDF.Statement(None, None, blank_node)):
            del model[s]
            model.append(RDF.Statement(s.subject, s.predicate, uri_node))            
        return
    
    
    @classmethod
    def rdf_identifier(cls, id_hash):
        return "%s/%s"%(cls.type, id_hash)

    @classmethod
    def get_unmapped_elements(cls, parent, model):

        if (not (parent and isinstance(parent, RDF.Node))):
            id_query = Template("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?child
            WHERE {
                ?child rdf:type <$type>
            }
            """).substitute(type=cls.type)

        else:
            id_query = Template("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?child
            WHERE {
                <$parent> ?predicate ?child.
                ?child rdf:type <$type>
            }
            """).substitute(type=cls.type, parent=parent.uri.__str__())

        ret = []
        for r in RDF.SPARQLQuery(id_query).execute(model):
            if r['child'].is_blank():
                ret.append(r['child'])
    
        return ret
    
        
class HashedMedicationFulfillment(HashedRDFUpdate):
    class Meta:
        proxy = True

    type=  "http://smartplatforms.org/med#fulfillment"
    child_classes = [ ]

    """
    Fulfillments are considered immutable.  Once they occur they never
    change, and never obtain new sub-properties.  (For now!)  So
    we consider a fulfillment to be completely described by its
    date-time, and won't overwrite or subdivide a fulfillment
    when new data arrives, as long as the datetime matches.
    """
    @classmethod
    def get_identifying_hash(cls, element, parent, model):
        id_query = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX med: <http://smartplatforms.org/med#>
        SELECT ?dispense_date
        WHERE {
            ?s rdf:type med:fulfillment.
            ?s dc:date ?dispense_date.
        }
        LIMIT 1
        """
        
        date = RDF.SPARQLQuery(id_query).execute(model).next()['dispense_date'].__str__()
        
        hash_base = "%s/%s"%(parent, date)       
        print "HashFulfillment: ", hash_base
        h = hashlib.sha224(hash_base).hexdigest()
        return h
    
            
class HashedMedication(HashedRDFUpdate):
    class Meta:
        proxy = True

    type = "http://smartplatforms.org/med#medication"
    child_classes= [HashedMedicationFulfillment]

    @classmethod
    def get_identifying_hash(cls, element, parent, model):
        id_query = Template("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX med: <http://smartplatforms.org/med#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        SELECT ?drug, ?notes, ?strength, ?title
        WHERE {
            <_:$element> med:drug ?drug.
        }
        
        LIMIT 1
        """).substitute(element=element.blank_identifier)
        
        result = RDF.SPARQLQuery(id_query).execute(model).next()
        drug = result['drug'].uri.__str__()
        notes = result['notes'] and result['notes'].literal_value['string']
        title = result['title'] and result['title'].literal_value['string']
        strength = result['strength'] and result['strength'].literal_value['string']
        
        hash_base = "%s/%s/%s/%s/%s"%(parent, drug, notes, title,strength)
        print "HashMEd: ", hash_base
        h = hashlib.sha224(hash_base).hexdigest()
        
        return h

