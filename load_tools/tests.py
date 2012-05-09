'''Module providing testing functionaly for the SMART API Verifier'''
# Developed by: Nikolai Schwertner
#
# Revision history:
#     2012-02-24 Initial release

# Standard module imports
import os
import unittest
import string
import json
import threading

# ISO 8601 date parser
# Make sure that you match the version of the library with your version
# of Python when you install it (Setup Tools / Easy Install does it incorrectly)
import dateutil.parser

# Enables automated sparql query generation from the ontology
import query_builder

# RDF parsing wrapper from the SMART python client
from smart_client.common.util import parse_rdf

# Global variables for state synchronization accross the test suites
lock = threading.Lock()
data = None
ct = None
currentModel = None

class TestDefault(unittest.TestCase):
    '''Default tests run on unidentified models'''
    
    def testUnknown(self):
        self.fail("Data model does not have an associated test suite")

class TestJSON(unittest.TestCase):
    '''Tests for JSON data parsing and content types'''
    
    def setUp(self):
        '''General tests setup (parses the JSON string in the global data var)'''
        try:
            self.json = json.loads(data)
        except:
            self.json = None

    def testValidJSON(self):
        '''Reports the outcome of the JSON parsing'''
        if not self.json:
            self.fail("JSON parsing failed")

    def testContentType(self):
        '''Verifies that the content type provided is application/json'''
        JSON_MIME = "application/json"
        self.assertEquals(ct, JSON_MIME, "HTTP content-type '%s' should be '%s'" % (ct, JSON_MIME))
                            
class TestManifestBase(unittest.TestCase):
    '''Common manifest structure tests'''

    def structure_validator (self, manifest):
        '''A simple structure test for a manifest's JSON'''
        
        if type(manifest) != dict:
            self.fail ("The manifest definition should be a dictionary")
        keys = manifest.keys()
        if "name" not in keys or not isinstance(manifest["name"], basestring) :
            self.fail ("All app manifests must have a 'name' string property")
        if "description" not in keys or not isinstance(manifest["description"], basestring) :
            self.fail ("All app manifests must have a 'description' string property")
        if "id" not in keys or not isinstance(manifest["id"], basestring) :
            self.fail ("All app manifests must have a 'id' string property")
        if "mode" not in keys or manifest["mode"] not in ("ui","background","frame_ui") :
            self.fail ("'mode' property must be one of ('ui','background','frame_ui')")
                    
class TestManifest(TestJSON, TestManifestBase):
    '''Tests for a single manifest'''

    def testStructure (self):
        '''Test for the manifests JSON output'''
        
        if self.json: self.structure_validator(self.json)
    

# Defines the mapping between the content models and the test suites
tests = {'Manifest': TestManifest}

def runTest(model, testData, contentType=None):
    '''Runs the test suite applicable for a model'''
    
    # The lock assures that any concurrent threads are synchronized so that
    # they don't interfere with each other through the global variables
    with lock:
    
        # Get hold of the global variables
        global data
        global ct
        global currentModel
        
        # Assign the input data to the globals
        data = testData
        ct = contentType
        currentModel = model
        
        # Load the test from the applicable test suite
        if model in tests.keys():
            alltests = unittest.TestLoader().loadTestsFromTestCase(tests[model])
        else:
            alltests = unittest.TestLoader().loadTestsFromTestCase(TestDefault)
        
        # Run the tests
        results = unittest.TextTestRunner(stream = open(os.devnull, 'w')).run(alltests)
        
        # Return the test results
        return results
    
def getMessages (results):
    '''Returns an array of strings representing the custom failure messages from the results'''
    
    res = []
    
    # Add all the failure messages to the array
    for e in results.failures:
        res.append ("[" + e[0]._testMethodName + "] " + getShortMessage(e[1]))
        
    # And then add all the error messages
    for e in results.errors:
        res.append ("[" + e[0]._testMethodName + "] " + e[1])

    return res

def getShortMessage (message):
    '''Returns the custom message portion of a unittest failure message'''
    
    s = message.split("AssertionError: ")
    return s[1]