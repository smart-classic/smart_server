"""
Rules for Accounts
"""

from smart.views import *

def check_my_account_wrapper(account):
    
    def check_my_account(request, view_func, view_args, view_kwargs):
        return view_kwargs['account_email'] == account.email

    return check_my_account

def check_record_account_wrapper(account):
    def check_record_account(request, view_func, view_args, view_kwargs):
        try:
            record = Record.objects.get(id = view_kwargs['record_id'])
            AccountRecord.objects.get(account = account, record = record)
        except Record.DoesNotExist, AccountRecordDoesNotExist:
            return False

        return True

    return check_record_account

def grant(account, permset):
    """
    grant the permissions of an account to this permset
    """

    check_my_account = check_my_account_wrapper(account)
    check_record_account = check_record_account_wrapper(account)

    permset.grant(home)

    # accounts
    permset.grant(account_info, [check_my_account])

    # see the record list
    permset.grant(record_list, [check_my_account])

    # see the notifications
    permset.grant(account_notifications, [check_my_account])

    # see the records
    permset.grant(record_info, [check_record_account])

    # see the apps in records
    permset.grant(record_apps, [check_record_account])

    # add and remove apps
    permset.grant(record_add_app, [check_record_account])
    permset.grant(record_remove_app, [check_record_account])
