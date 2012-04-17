"""
Rules for PHAs, AccessTokens, ReqTokens
"""

from smart.views import *

def check_my_app_wrapper(pha):
        def check_my_app(request, view_func, view_args, view_kwargs):
            return view_kwargs['pha_email'] == pha.email
        return check_my_app

def grant(pha, permset):
    """
    grant the permissions of an account to this permset
    """
    
    check_my_app = check_my_app_wrapper(pha)

    permset.grant(request_token, None)
    permset.grant(session_create, None)

