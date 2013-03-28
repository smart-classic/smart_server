"""
Rules for Accounts
"""

from smart.views import *

def grant(machineapp, permset):
    """
    grant the permissions of an account to this permset
    """

    permset.grant(user_create, None)
    permset.grant(session_create, None)
    permset.grant(request_token_claim, None)
    permset.grant(request_token_info, None)
    permset.grant(user_reset_password, None)
    permset.grant(user_reset_password_request, None)
    
    permset.grant(create_proxied_record, None)
    permset.grant(generate_direct_url, None)
    permset.grant(session_from_direct_url, None)
    
    permset.grant(resolve_manifest, None)
    permset.grant(manifest_delete, None)
    permset.grant(manifest_put, None)
    permset.grant(all_manifests, None)
    permset.grant(app_oauth_credentials, None)
