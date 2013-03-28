#!/usr/bin/env python

from django.conf import settings
from smart.models import *
from smart.lib.utils import get_capabilities, random_string
from string import Template
import re
import sys
import os
from django.utils import simplejson
import urllib2

# Import the manifest validator function
from smart.common.utils.manifest_tests import app_manifest_structure_validator


def sub(str, var, val):
    return str.replace("{%s}" % var, val)


def LoadApp(app_params):
    # Some basic apps and a couple of accounts to get things going.
    app = app_params["manifest"]
    print app
    if not app.startswith("http"):
        s = open(app)
    else:
        s = urllib2.urlopen(app)

    manifest_string = s.read()
    s.close()
    return LoadAppFromJSON(manifest_string, app_params)


def LoadAppFromJSON(manifest_string, app_params=None):
    """ Reads an app manifest
    """
    if app_params == None:
        app_params = {}

    if "secret" not in app_params:
        print "No consumer secret among the app params. Generating consumer secret."
        app_params["secret"] = random_string(16)

    r = simplejson.loads(manifest_string)
    secret = app_params["secret"]

    messages = app_manifest_structure_validator(r)
    if len(messages) > 0:
        msg = "WARNING! This app manifest is invalid: %s (app %s)" % ('. '.join(messages), r['id'])
        raise Exception(msg)

    if "override_index" in app_params:
        r["index"] = app_params["override_index"]

    if "override_icon" in app_params:
        r["icon"] = app_params["override_icon"]

    enabled_by_default = False
    if "enabled_by_default" in app_params:
        enabled_by_default = app_params["enabled_by_default"]

    manifest_string = json.dumps(r, sort_keys=True, indent=4)

    # background app
    if r["mode"] in ("background", "helper"):
        a = HelperApp.objects.create(
            description=r["description"],
            consumer_key=r["id"],
            secret=secret,
            name=r["name"],
            email=r["id"],
            manifest=manifest_string
        )

    # ui app
    elif r["mode"] in ("ui", "frame_ui"):

        # extract optimal environments
        if "optimalBrowserEnvironments" not in r:
            r["optimalBrowserEnvironments"] = ["desktop"]
        if "supportedBrowserEnvironments" not in r:
            r["supportedBrowserEnvironments"] = ["desktop", "mobile", "tablet"]
        opt_browsers = ",".join(r["optimalBrowserEnvironments"])
        sup_browsers = ",".join(r["supportedBrowserEnvironments"])
        
        # extract standalone
        is_standalone = False
        if "standalone" in r:
            is_standalone = r["standalone"]

        exists = PHA.objects.filter(email=r["id"])
        assert len(exists) < 2, "Found >1 PHA by the name %s" % r["id"]
        if len(exists) == 1:
            print exists[0]
            print "deleting, exists."
            exists[0].delete()
        
        a = PHA.objects.create(
            description=r["description"],
            consumer_key=r["id"],
            secret=secret,
            name=r["name"],
            email=r["id"],
            mode=r["mode"],
            standalone=is_standalone,
            icon_url=r["icon"],
            enabled_by_default=enabled_by_default,
            optimal_environments=opt_browsers,
            supported_environments=sup_browsers,
            manifest=manifest_string
        )
    else:
        a = None

    # should probably return here if no App was created
    if a is None:
        return None


    if "requires" in r:
        capabilities = get_capabilities()
        for k in r["requires"]:
            if k not in capabilities:
                print "WARNING! This app requires an unsupported datatype:", k
                break
            for m in r["requires"][k]["methods"]:
                if m not in capabilities[k]["methods"]:
                    print "WARNING! This app requires an unsupported method:", k, m

    if "smart_version" in r:
        if r["smart_version"] != settings.VERSION:
            print "WARNING! This app requires SMART version", r["smart_version"]

    return a

if __name__ == "__main__":
    import string
    v = sys.argv[1]
    secret = None

    if len(sys.argv) > 2:
        secret = sys.argv[2]

    print "Loading apps via load_one_app is deprecated.  Please use 'python manage.py load_app' instead."
    print "Loading app: %s" % v

    app_params = {
        "manifest": v,
    }
    if secret:
        app_params["secret"] = secret

    a = LoadApp(app_params)
    print "Loaded app with secret: %s" % a.secret
