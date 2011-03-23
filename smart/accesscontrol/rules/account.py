"""
Rules for Accounts
"""

from smart.views import *

def check_my_account_wrapper(account):
    
    def check_my_account(request, view_func, view_args, view_kwargs):
        return view_kwargs['account_email'] == account.email

    return check_my_account


def grant(account, permset):
    """
    grant the permissions of an account to this permset
    """

    check_my_account = check_my_account_wrapper(account)

    permset.grant(home)

    # accounts
    permset.grant(account_info, [check_my_account])

    # see the record list
    permset.grant(record_list, [check_my_account])

    # see the records
    permset.grant(record_info, [])

    # see the apps in records

    # add and remove apps
    permset.grant(add_app, [])
    permset.grant(launch_app, [])
    permset.grant(remove_app, [])
    
    # Claiming a request token is free
    permset.grant(request_token_claim, None)
    permset.grant(request_token_approve, None) # need to verify record ID?
    permset.grant(request_token_info, None) # need to verify exists?
    permset.grant(account_recent_records, [check_my_account])
    permset.grant(record_search_xml, [])
    permset.grant(apps_for_account, [])
    permset.grant(resolve_activity, [])
    permset.grant(resolve_activity_with_app, [])
    
    
