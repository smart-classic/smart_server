"""
Indivo Views -- Base

Ben Adida
"""

from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseBadRequest
from django.contrib.auth.models import User

from django.core.exceptions import *
from django.core import serializers
from django.db import transaction

from smart.models import *
from smart.accesscontrol.security import *
from smart.lib.view_decorators import paramloader, marsloader

import logging, datetime

# SZ: standardize
from smart.lib import utils
from smart.lib.utils import render_template, render_template_raw

DONE = render_template('ok', {}, type="xml")
