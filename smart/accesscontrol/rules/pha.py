"""
Rules for PHAs, AccessTokens, ReqTokens
"""

from smart.views import *
from smart.views.smarthacks import *

def grant(principal, permset):
    """
    grant the permissions of an account to this permset
    """

    permset.grant(request_token, None)
    permset.grant(session_create, None)
    permset.grant(rdf_store, None)
    permset.grant(rdf_query, None)
    permset.grant(rdf_dump, None)
    