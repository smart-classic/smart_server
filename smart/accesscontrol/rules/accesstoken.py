"""
Rules for Accounts
"""

from smart.views import *
from smart.models.rdf_rest_operations import *
from smart.models.record_object import *

try:
    from smart.plugins import *  
except ImportError: pass

def check_token_for_record_wrapper(token):
        def check_token_for_record(request, view_func, view_args, view_kwargs):
            return token.share.record.id == view_kwargs['record_id']
        return check_token_for_record

def check_frame_mode_wrapper(token):
    pha = PHA.objects.get(id=token.share.with_app.id)
    
    def r(request, view_func, view_args, view_kwargs):
        return pha.mode == "frame_ui"
    return r
    
def check_token_for_account_app_wrapper(token):
        def check_token_for_account_app(request, view_func, view_args, view_kwargs):
            pha = PHA.objects.get(id=token.share.with_app.id)
            acc = Account.objects.get(id=token.share.authorized_by.id)
            return pha.email == view_kwargs['pha_email'] and acc.email == view_kwargs['account_email']
        return check_token_for_account_app

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
    permset.grant(record_get_allergies, [check_token_for_record])

    try:
        permset.grant(record_proxy_backend.proxy_get, [check_token_for_record])
    except: 
        pass
    
    permset.grant(put_demographics, [check_token_for_record])
    permset.grant(record_post_alert, [check_token_for_record])
    permset.grant(user_search)
    permset.grant(user_get)
    

    check_frame_mode = check_frame_mode_wrapper(accesstoken)
    permset.grant(resolve_activity_with_app, [])
    permset.grant(resolve_manifest, [check_frame_mode])
    permset.grant(all_manifests, [check_frame_mode])
    permset.grant(record_search, [check_frame_mode])

    check_token_for_account_app = check_token_for_account_app_wrapper(accesstoken)
    permset.grant(preferences_get, [check_token_for_account_app])
    permset.grant(preferences_put, [check_token_for_account_app])
    permset.grant(preferences_delete, [check_token_for_account_app])