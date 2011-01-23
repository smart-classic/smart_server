"""
Management of the App, hooks for django

Ben Adida
2008-12-02
"""

from django.dispatch import dispatcher
from django.db.models import get_models, signals

def setup_bootstrap(app, created_models, verbosity, **kwargs):
  import bootstrap

# add the dispatcher to set things up
signals.post_syncdb.connect(setup_bootstrap)
