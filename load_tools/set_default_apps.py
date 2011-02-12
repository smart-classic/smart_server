from smart.models import *
for ac in Account.objects.all():
  for ap in PHA.objects.all():
    if ap.enabled_by_default:
      AccountApp.objects.get_or_create(account=ac,app=ap)
 
