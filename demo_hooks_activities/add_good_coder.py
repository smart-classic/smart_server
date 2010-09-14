from smart.models import *
ah = AppActivity.objects.filter(name='reconcile_medications')[0]
a = ah.app
ah.delete()
ah = AppActivity.objects.create(app=a, name='reconcile_medications', description='', url='http://localhost:8001/med_coder.html')
print "Added good coder"
