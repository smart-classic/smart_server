"""
Rules for Accounts
"""

from smart.views import *
from smart.models.rdf_rest_operations import *
from smart.models.record_object import record_get_filtered_labs
from smart.models.record_proxy_backend import proxy_get

def check_token_for_record_wrapper(token):
        def check_token_for_record(request, view_func, view_args, view_kwargs):
            return token.share.record.id == view_kwargs['record_id']
        return check_token_for_record


def grant(accesstoken, permset):
    """
    grant the permissions of an account to this permset
    """
    
    check_token_for_record = check_token_for_record_wrapper(accesstoken)

    permset.grant(home)
    permset.grant(record_by_token)

    permset.grant(do_webhook)
    permset.grant(record_delete_all_objects, [check_token_for_record])
    permset.grant(record_delete_object, [check_token_for_record])
    permset.grant(record_put_object, [check_token_for_record])
    permset.grant(record_post_objects, [check_token_for_record])
    permset.grant(record_get_all_objects, [check_token_for_record])

    permset.grant(record_get_object, [check_token_for_record])
    permset.grant(record_get_filtered_labs, [check_token_for_record])
    permset.grant(proxy_get, [check_token_for_record])

    permset.grant(put_demographics, [check_token_for_record])
    permset.grant(user_search)
    permset.grant(user_get)
    
    
