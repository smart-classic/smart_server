"""
Records for SMART Reference EMR

Ben Adida & Josh Mandel
"""

from base import *
from django.utils import simplejson
from django.conf import settings
from smart.common.rdf_tools.rdf_ontology import ontology
from smart.common.rdf_tools.util import rdf, foaf, vcard, sp, serialize_rdf, parse_rdf, bound_graph, URIRef, Namespace
from smart.lib import utils
from smart.models.apps import *
from smart.models.accounts import *
from smart.triplestore import *
from string import Template
import re
import datetime


class Record(Object):
    Meta = BaseMeta()

    full_name = models.CharField(max_length=150, null=False)

    def __unicode__(self):
        return 'Record %s' % self.id

    def generate_direct_access_token(self, account, token_secret=None):
        u = RecordDirectAccessToken.objects.create(
            record=self,
            account=account,
            token_secret=token_secret
        )
        u.save()
        return u

    @classmethod
    def search_records(cls, query):
        try:
            c = TripleStore()
            ids = parse_rdf(c.sparql(query))
        except Exception, e:
            return None

        from smart.models.record_object import RecordObject
        demographics = RecordObject[sp.Demographics]
        subjects = [p[0] for p in ids.triples((None, rdf['type'],
                                              sp.Demographics))]
        ret = c.get_contexts(subjects)
        return ret

    @classmethod
    def rdf_to_objects(cls, res):
        if res is None:
            return None
        m = parse_rdf(res)

        record_list = []

        q = """
PREFIX sp:<http://smartplatforms.org/terms#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dcterms:<http://purl.org/dc/terms/>
PREFIX v:<http://www.w3.org/2006/vcard/ns#>
PREFIX foaf:<http://xmlns.com/foaf/0.1/>

SELECT ?gn ?fn ?dob ?gender ?zipcode ?d
WHERE {
    ?d rdf:type sp:Demographics.
    ?d v:n ?n.
    ?n v:given-name ?gn.
    ?n v:family-name ?fn.
    optional{?d foaf:gender ?gender.}
    optional{?d v:bday ?dob.}

    optional{
        ?d v:adr ?a.
        ?a rdf:type v:Pref.
        ?a v:postal-code ?zipcode.
    }

    optional{
        ?d v:adr ?a.
        ?a v:postal-code ?zipcode.
    }
}"""

        people = list(m.query(q))
        for p in people:
            record = Record()
            record.id = re.search(
                "\/records\/(.*?)\/demographics", str(p[5])).group(1)
            record.fn, record.ln, record.dob, record.gender, record.zipcode = p[:5]
            record_list.append(record)

        return record_list


class AccountApp(Object):
    account = models.ForeignKey(Account)
    app = models.ForeignKey(PHA)

    # uniqueness
    class Meta:
        app_label = APP_LABEL
        unique_together = (('account', 'app'),)


# Not an OAuth token, but an opaque token that can be used to support
# auto-login via a direct link to a smart_ui_server.
class RecordDirectAccessToken(Object):
    record = models.ForeignKey(
        Record, related_name='direct_access_tokens', null=False)
    account = models.ForeignKey(
        Account, related_name='direct_record_shares', null=False)
    token = models.CharField(max_length=40, unique=True)
    token_secret = models.CharField(max_length=60, null=True)
    expires_at = models.DateTimeField(null=False)

    def save(self, *args, **kwargs):

        if not self.token:
            self.token = utils.random_string(30)

        if self.expires_at is None:
            minutes_to_expire = 30
            try:
                minutes_to_expire = settings.MINUTES_TO_EXPIRE_DIRECT_ACCESS
            except:
                pass

            self.expires_at = datetime.datetime.utcnow(
            ) + datetime.timedelta(minutes=minutes_to_expire)
        super(RecordDirectAccessToken, self).save(*args, **kwargs)

    class Meta:
        app_label = APP_LABEL


class RecordAlert(Object):
    record = models.ForeignKey(Record)
    alert_text = models.TextField(null=False)
    alert_time = models.DateTimeField(auto_now_add=True, null=False)
    triggering_app = models.ForeignKey(
        'OAuthApp', null=False, related_name='alerts')
    acknowledged_by = models.ForeignKey('Account', null=True)
    acknowledged_at = models.DateTimeField(null=True)

    # uniqueness
    class Meta:
        app_label = APP_LABEL

    @classmethod
    def from_rdf(cls, rdfstring, record, app):
        s = parse_rdf(rdfstring)

        q = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX sp: <http://smartplatforms.org/terms#>
        SELECT ?notes ?severity
        WHERE {
            ?a rdf:type sp:Alert.
            ?a sp:notes ?notes.
            ?a sp:severity ?scv.
            ?scv sp:code ?severity.
        }"""

        r = list(s.query(q))
        assert len(r) == 1, "Expected one alert in post, found %s" % len(r)
        (notes, severity) = r[0]

        assert type(notes) == Literal
        spcodes = Namespace("http://smartplatforms.org/terms/code/alertLevel#")
        assert severity in [spcodes.information, spcodes.warning,
                            spcodes.critical]

        a = RecordAlert(
            record=record,
            alert_text=str(notes),
            triggering_app=app
        )
        a.save()
        return a

    def acknowledge(self, account):
        self.acknowledged_by = account
        self.acknowledged_at = datetime.datetime.now()
        self.save()


class LimitedAccount(Account):
    records = models.ManyToManyField(Record, related_name="+")
