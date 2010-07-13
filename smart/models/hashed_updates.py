"""
Records for SMArt bootstrap

Ben Adida
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
      return 'HashedRDFUpdate:   id=%s, identifying_hash=%s, complete_hash=%s' % (
              self.id, 
              self.identifying_hash, 
              self.complete_hash)
    
    """
    Element is a node in the RDF modeled by data.
    """
    @classmethod
    def conditional_create(cls, model=RDF.Model(),context=None):
#        print "Conditionally creating ", cls.type, " with context ", context
        for blank_node in cls.get_unmapped_elements(parent=context, model=model):      
            id_hash = cls.get_identifying_hash(element=blank_node, parent=context, model=model)
            partially_inserted=None
            fully_inserted = None
            try:
                partially_inserted = cls.objects.get(identifying_hash=id_hash)  
            except:
                fully_inserted = cls(identifying_hash=id_hash,
                                     data=utils.serialize_rdf(model),
                                     uri_string="%s/%s"%(cls.type, id_hash))
    
            inserted = partially_inserted or fully_inserted
            cls.remap_blank_node(model, blank_node.blank_identifier, inserted.uri_string)

            for child_class in cls.child_classes:
                child_class.conditional_create(context=RDF.Node(uri_string=inserted.uri_string), 
                                               model=model)

    @classmethod 
    def remap_blank_node(cls, model, blank_string, uri_string):
        uri_node = RDF.Node(uri_string=uri_string)
        blank_node = RDF.Node(blank=blank_string)
        for s in model:
            new_s = s.subject
            new_o = s.object
            remapped = False
            if (s.subject == blank_node):
                remapped = True
                new_s = uri_node
            if (s.object == blank_node):
                remapped = True
                new_o = uri_node
            if (remapped):
                del model[s]
                model.append(RDF.Statement(new_s, s.predicate, new_o))
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
            }""").substitute(type=cls.type)

        else:
            id_query = Template("""
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT ?child
            WHERE {
                <$parent> ?predicate ?child.
                ?child rdf:type <$type>
            }""").substitute(type=cls.type, parent=parent.uri.__str__())

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
        h = hashlib.sha224(hash_base).hexdigest()
        return h
    
            
class HashedMedication(HashedRDFUpdate):
    class Meta:
        proxy = True

    type = "http://smartplatforms.org/med#medication"
    child_classes= [HashedMedicationFulfillment ]

    @classmethod
    def get_identifying_hash(cls, element, parent, model):
        id_query = Template("""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX med: <http://smartplatforms.org/med#>
        SELECT ?drug
        WHERE {
            <_:$element> med:drug ?drug
        }
        LIMIT 1
        """).substitute(element=element.blank_identifier)
        
        drug = RDF.SPARQLQuery(id_query).execute(model).next()['drug'].uri.__str__()
        hash_base = "%s/%s"%(parent, drug)       
        h = hashlib.sha224(hash_base).hexdigest()
        
        return h
