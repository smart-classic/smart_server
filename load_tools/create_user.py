from smart.models.accounts import *
from django.conf import settings
import sys

"""
To run:

PYTHONPATH=/path/to/smart_server \
  DJANGO_SETTINGS_MODULE=settings \
  /usr/bin/python \
  load_tools/load_one_patient.py \
  given_name family_name email@host.com password
"""


if __name__ == "__main__":

    given_name = sys.argv[1]
    family_name = sys.argv[2]
    email = sys.argv[3]
    password = sys.argv[4]

    new_account, create_p = Account.objects.get_or_create(email=email)

    if not create_p:
        sys.exit()

    if create_p:
        new_account.given_name = given_name
        new_account.family_name = family_name

    new_account.contact_email = email
    new_account.set_username_and_password(email, password)
    new_account.save()
