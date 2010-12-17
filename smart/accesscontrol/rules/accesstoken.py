"""
Rules for Accounts
"""

from smart.views import *
from smart.models.rdf_rest_operations import *

def grant(accesstoken, permset):
    """
    grant the permissions of an account to this permset
    """

    permset.grant(home)
    permset.grant(record_by_token)

    permset.grant(do_webhook)
    permset.grant(record_delete_all_objects)
    permset.grant(record_delete_object)
    permset.grant(record_put_object)
    permset.grant(record_post_objects)
    permset.grant(record_get_all_objects)
    permset.grant(record_get_object)
    
    permset.grant(put_demographics)