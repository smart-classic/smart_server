from smart.models import *

def remap_app(current_user_id, current_url):
  user = Account.objects.get(email=current_user_id)
  my_cloud = AppActivity.objects.get(app__email='my-cloud-app@apps.smartplatforms.org', name='main')
  remap,created = PrincipalActivityRemaps.objects.get_or_create(principal=user, activity=my_cloud, defaults={'url': current_url})
  remap.url = current_url
  remap.save()

if __name__ == "__main__":
   import sys  
   user_account = sys.argv[1]
   new_url = sys.argv[2]
   print "Updating my-cloud-app mapping: %s --> %s"%(user_account, new_url)
   remap_app(sys.argv[1], sys.argv[2])
