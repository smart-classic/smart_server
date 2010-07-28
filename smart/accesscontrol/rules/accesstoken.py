"""
Rules for Accounts
"""

from smart.views import *

def grant(accesstoken, permset):
    """
    grant the permissions of an account to this permset
    """

    permset.grant(home)
    permset.grant(record_by_token)

    permset.grant(post_rdf_meds)
    permset.grant(get_rdf_meds)
    permset.grant(put_rdf_meds)
    permset.grant(delete_rdf_meds)

    permset.grant(post_rdf_problems)
    permset.grant(get_rdf_problems)
    permset.grant(put_rdf_problems)
    permset.grant(delete_rdf_problems)
