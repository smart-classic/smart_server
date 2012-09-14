"""
remove accesstokens and sessiontokens that are expired.
"""


from django.core.management.base import BaseCommand, CommandError
from smart_server.load_tools.load_one_app import LoadApp

class Command(BaseCommand):
    args = 'manifest_location consumer_secret'
    help = 'Load a new app, given an external manifest (local file or http address) and a consumer_secret'

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
    
        assert len(args)>0, "Expected manifest_location and an optional consumer_secret"

        l = args[0]
        s = None

        if len(args)>1:
            s = args[1]

        
        def print_if(stmt, min_verbosity=1):
            if verbosity > min_verbosity:
                print stmt
                
        print_if("Loding app from %s..."%l)
        params = {'manifest': l}
        if s:
            params['secret'] = s

        a = LoadApp(params)
        print_if("Loaded app with secret: %s"%a.secret)
