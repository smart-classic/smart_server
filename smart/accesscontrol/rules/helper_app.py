"""
Rules for PHAs, AccessTokens, ReqTokens
"""

from smart.views import *

def grant(happ, permset):
    """
    grant the permissions of an account to this permset
    """
    permset.grant(get_first_record_tokens, None)
    permset.grant(get_next_record_tokens, None)
    permset.grant(get_record_tokens, None)
    
    permset.grant(download_ontology, None)