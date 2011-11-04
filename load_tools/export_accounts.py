#!/usr/bin/env python

import os
os.system("python manage.py dumpdata smart.account smart.AuthSystem smart.AccountAuthSystem smart.Principal > accounts.json")

from django.utils import simplejson
f = open("accounts.json")
r = simplejson.load(f)
f.close()

passed = []
for t in r:
  if t['model'] == 'smart.principal':
    if t['fields']['type'] == 'Account':
      passed.append(t)
  else:
    passed.append(t)

f = open("accounts.json", "w")
simplejson.dump(passed, f)
f.close()
