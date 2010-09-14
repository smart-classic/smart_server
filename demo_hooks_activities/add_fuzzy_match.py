from smart.models import *
ah = AppWebHook.objects.all()[0]
a = ah.app
ah.delete()
ah = AppWebHook.objects.create(app=a, name='fuzzy_match_rxnorm', description='webhook to  confidently match a text description of a drug to a set of matching RxNorm Concepts', url='http://localhost:8001/webhook/fuzzy_match_rxnorm')
print "Added confident match"
