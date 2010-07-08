
from smart.models import *

##
## Set up some basic stuff
##

MachineApp.objects.create(name='chrome',
                          consumer_key='chrome',
                          secret='chrome',
                          app_type='chrome',
                          email='chrome@apps.smart-project.org')

PHA.objects.create(start_url_template= 'http://localhost:8001/index.html?record_id={record_id}&account_id={account_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'List patient\'s medications plus supplementary details',
                   consumer_key = 'smart-fg-app',
                   secret = 'smartapp-secret',
                   name ='MedList',
                   email='medlist@apps.smart.org')


PHA.objects.create(start_url_template= 'http://localhost:8001/statin.html?record_id={record_id}&account_id={account_id}',
                   callback_url = 'http://localhost:8001/auth/after',
                   has_ui = True,
                   frameable = True,
                   description = 'States whether patient is taking a statin.',
                   consumer_key = 'smart-statin-app',
                   secret = 'smartapp-secret',
                   name ='Am-I-on-a-Statin?',
                   email='am-i-on-a-statin@apps.smart.org')


PHA.objects.create(start_url_template= 'http://localhost:8002/smart/start_auth?record_id={record_id}&account_id={account_id}',
                   callback_url = 'http://localhost:8002/smart/after_auth',
                   has_ui = True,
                   frameable = True,
                   description = 'Keeps SMArt updated from a SureScripts feed (long-term, runs in background)',
                   consumer_key = 'smart-bg-app',
                   secret = 'smartapp-secret',
                   name ='SureScripts Sync',
                   email='surescripts-sync@apps.smart.org',
                   background_p=True)

a = Account.objects.create(email = 'benadida@smart.org', full_name='Ben Adida', contact_email = 'ben@adida.net')
a.set_username_and_password(username='benadida', password='test')

# create a couple of records
r_john = Record.objects.create(full_name = 'John Doe')
r_jane = Record.objects.create(full_name = 'Jane Doe')

# map these to the account I have
#AccountRecord.objects.create(record = r_john, account = a)
#AccountRecord.objects.create(record = r_jane, account = a)

a2 = Account.objects.create(email = 'joshmandel@smart.org', full_name='Josh Mandel', contact_email = 'jmandel@gmail.com')
a2.set_username_and_password(username='joshmandel', password='test')

# create a couple of records
r_john = Record.objects.create(full_name = 'John Smith')
r_jane = Record.objects.create(full_name = 'Jane Smith')

# map these to the account I have
#AccountRecord.objects.create(record = r_john, account = a2)
#AccountRecord.objects.create(record = r_jane, account = a2)

