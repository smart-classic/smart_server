"""
Rules for PHAs, AccessTokens, ReqTokens
"""

from smart.views import *

def grant(happ, permset):
    """
    grant the permissions of an account to this permset
    """

    def need_admin(*a,**b): return happ.admin_p

    permset.grant(get_first_record_tokens, None)
    permset.grant(get_next_record_tokens, None)
    permset.grant(get_record_tokens, None)
    permset.grant(download_ontology, None)
    permset.grant(record_search, [need_admin])
    permset.grant(record_post_objects, [need_admin])
#    permset.grant(put_demographics, [need_admin])
