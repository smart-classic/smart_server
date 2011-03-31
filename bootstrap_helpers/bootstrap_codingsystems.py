from bootstrap_utils import interpolated_postgres_load
import os
from django.conf import settings
from smart.models import *

interpolated_postgres_load(
    os.path.join(settings.APP_HOME, "codingsystems/data/load-snomedctcore.sql"),
    {"snomed_core_data": 
     os.path.join(settings.APP_HOME, 
                  "codingsystems/data/complete/SNOMEDCT_CORE_SUBSET_201005.utf8.txt")},
    settings.DATABASE_NAME,
    settings.DATABASE_USER
)
