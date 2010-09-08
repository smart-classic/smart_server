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

    permset.grant(record_sparql)

    permset.grant(record_problems_get)
    permset.grant(record_problems_post)
    permset.grant(record_problems_delete)
    
    permset.grant(record_problem_get)
    permset.grant(record_problem_get_external)
    permset.grant(record_problem_put)
    permset.grant(record_problem_delete)
    permset.grant(record_problem_delete_external)
    
        
    permset.grant(record_meds_get)
    permset.grant(record_meds_post)
    permset.grant(record_meds_delete)
    
    permset.grant(record_med_get)
    permset.grant(record_med_get_external)
    permset.grant(record_med_put)
    permset.grant(record_med_post)
    permset.grant(record_med_delete)
    permset.grant(record_med_delete_external)
    
    
    permset.grant(record_med_fulfillments_get)
    permset.grant(record_med_fulfillments_post)
    
    permset.grant(record_med_fulfillment_get)
    permset.grant(record_med_fulfillment_delete)
    
    permset.grant(record_med_fulfillment_delete_external)
    permset.grant(record_med_fulfillment_get_external)
    permset.grant(record_med_fulfillment_put_external)


    permset.grant(do_intent)
