"""
Rules for Accounts
"""

from smart.views import *

def grant(machineapp, permset):
    """
    grant the permissions of an account to this permset
    """

    permset.grant(account_create, None)
    permset.grant(session_create, None)
    permset.grant(request_token_claim, None)
    permset.grant(request_token_info, None)
    
