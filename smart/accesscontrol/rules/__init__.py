"""
A directory of rules
"""

import account, principal, accesstoken, machineapp
import smart.models as models

RULES = {}
RULES[models.Account] = account
RULES[models.Principal] = principal
RULES[models.MachineApp] = machineapp
# access token FIXME

def get_module_by_principal(principal):
    return RULES[principal.__class__]

def grant_by_principal(principal, permset):
    get_module_by_principal(principal).grant(principal, permset)
