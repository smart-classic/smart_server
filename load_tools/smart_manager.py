#!/usr/bin/env python

import sys
import os
import platform
import re
import imp
import subprocess
import logging
import argparse
import string
import urlparse
import django

from random import choice

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

cwd = os.getcwd()
PASSWORD_LETTERBANK = string.letters + string.digits
PASSWORD_LETTERBANK = PASSWORD_LETTERBANK.replace("O", "")

def get_input(p, d):
    v = raw_input("\n%s [%s]: "%(p, d))
    if v: return v
    return d

def do_sed(t,n,v):
    v =  re.sub("/", r'\/', v)

    if platform.system() == 'Darwin':
      c = "sed -i '' -e's/%s/%s/' %s" % (n, v, t)
    else:
      c = "sed -i -e's/%s/%s/' %s" % (n, v, t)

    o = call_command(c)
    print o
    return o

def fill_field(t, n, v):
    return do_sed(t, "{{%s}}"%n, v)

def main():
    parser = argparse.ArgumentParser(description='SMART Server Management Tool')

    parser.add_argument("-a", "--all-steps", dest="all_steps",
                    action="store_true",
                    default=False,
                    help="All steps: clone, generate settings, "+
                      "kill running servers, generate sample data, "+
                      "run app server, reset api server, "+
                      "load sample data, run api servers")

    parser.add_argument("-b", "--branch", dest="using_branch",
                    default=False,
                    help="Use a specific branch for checkouts and updates")

    parser.add_argument("-d", "--development-branch", dest="branch_dev",
                    action="store_true",
                    default=False,
                    help="Use development branch for checkous and updates")
                      
    parser.add_argument("-g", "--clone-git-repositories", dest="clone_git",
                    action="store_true",
                    default=False,
                    help="Clone git repositories")
                    
    parser.add_argument("-u", "--update-git-repositories", dest="update_git",
                    action="store_true",
                    default=False,
                    help="Update git repositories")

    parser.add_argument("-s", "--generate-settings-files", dest="generate_settings",
                    action="store_true",
                    default=False,
                    help="Generate settings files")
                    
    parser.add_argument("-k", "--kill-servers", dest="kill_servers",
                    action="store_true",
                    default=False,
                    help="Kill all currently-running django development servers")
                      
    parser.add_argument("-p", "--generate-sample-data", dest="generate_sample_data",
                    action="store_true",
                    default=False,
                    help="Generate sample patient data")

    parser.add_argument("-v", "--run-app-server", dest="run_app_server",
                    action="store_true",
                    default=False,
                    help="Run app server (first kills all running SMART servers). Can be used in conjunction with -w")
    
    parser.add_argument("-r", "--reset-api-server", dest="reset_servers",
                    action="store_true",
                    default=False,
                    help="Reset API server")
                    
    parser.add_argument("-l", "--load-sample-data", dest="load_sample_data",
                    action="store_true",
                    default=False,
                    help="Load sample data into DB")
                    
    parser.add_argument("-c", "--create-user", dest="create_user",
                    action="store_true",
                    default=False,
                    help="Create a user account for web login")
    
    parser.add_argument("-w", "--run-api-servers", dest="run_api_servers",
                    action="store_true",
                    default=False,
                    help="Run api server (first kills all running SMART servers). Can be used conjunction with -v")

    args = parser.parse_args()
    repos = ["smart_server", "smart_ui_server", "smart_sample_patients", "smart_sample_apps"]

    reloadflag = ""
    if django.VERSION[:3] <= (1,3,0):
        reloadflag = " --noreload "

    if args.branch_dev:
        args.using_branch = "dev"
    if args.using_branch:
       print "USING BRANCH", args.using_branch
    if not args.all_steps and not ( 
        args.clone_git or
        args.update_git or
        args.generate_settings or
        args.generate_sample_data or
        args.load_sample_data or
        args.create_user or 
        args.kill_servers or
        args.reset_servers or
        args.run_app_server or 
        args.run_api_servers):
            parser.print_help()
            sys.exit(1)

    if args.all_steps:
        args.clone_git = True
        args.generate_settings  = True
        args.generate_sample_data  = True
        args.load_sample_data  = True
        args.create_user = True
        args.kill_servers = True
        args.run_app_server = True
        args.reset_servers  = True
        args.run_api_servers = True

    if args.clone_git:
        if not args.using_branch:
            args.using_branch = "master"

        print "Cloning (4) SMART git repositories..."
        for r in repos:
            call_command("git clone --recursive --recurse-submodules https://github.com/smart-platforms/"+r+".git", 
                        print_output=True)

    if args.update_git or args.clone_git:
        for r in repos:

            if args.using_branch:
                call_command("cd "+r+" && git checkout "+args.using_branch+" && cd ..")

            call_command("cd "+r+" && " +
                     "git pull && " +
                     "git submodule update --init --recursive && " +
                     "cd .. ",
                      print_output=True)
        
    if args.generate_settings:
        print "Configuring SMART server settings..."

        api_server_base_url = get_input("SMART API Server", "http://localhost:7000")
        
        chrome_consumer = get_input("Chrome App Consumer ID", "chrome")
        
        chrome_secret = get_input("Chrome App Consumer secret",  
                                  ''.join([choice(PASSWORD_LETTERBANK) for i in range(8)]))

        # TO DO: The password should be random here, but somehow we need to be able to change the DB password to match
        db_password = get_input("Database User Password",  "smart")          

        ui_server_base_url = get_input("SMART UI server", "http://localhost:7001")
        app_server_base_url = get_input("SMART App server", "http://localhost:8001")
        
        standalone_mode = get_input(
            """Run server in standalone mode (patient data stored in local db)?  
            If you choose 'no', the server will be configured in proxy mode, 
            with patient data hosted at a REST URL you provide.""", "yes")

        if standalone_mode=="no":
            proxy_base = get_input("Proxy server to use for medical record data",
                                   "none")

            proxy_user = get_input("User to associate with proxied requests", 
                                   "proxy_user@smartplatforms.org")
        
        call_command("cp smart_server/settings.py.default smart_server/settings.py")

        call_command("cp smart_server/bootstrap_helpers/application_list.json.default " + 
                            "smart_server/bootstrap_helpers/application_list.json ")
                            
        call_command("cp smart_server/bootstrap_helpers/bootstrap_applications.py.default " + 
                            "smart_server/bootstrap_helpers/bootstrap_applications.py ")
                   
        fill_field('smart_server/bootstrap_helpers/application_list.json', 'app_server_base_url', app_server_base_url)
        fill_field('smart_server/bootstrap_helpers/bootstrap_applications.py', 'app_server_base_url', app_server_base_url)
        fill_field('smart_server/bootstrap_helpers/bootstrap_applications.py', 'ui_server_base_url', ui_server_base_url)

        call_command("cp smart_ui_server/settings.py.default smart_ui_server/settings.py")
        call_command("cp smart_sample_apps/settings.py.default smart_sample_apps/settings.py")

        fill_field('smart_server/settings.py', 'path_to_smart_server', 
                   os.path.join(cwd, "smart_server"))
        
        fill_field('smart_ui_server/settings.py', 'path_to_smart_ui_server', 
                   os.path.join(cwd, "smart_ui_server"))
        
        fill_field('smart_sample_apps/settings.py', 'path_to_smart_sample_apps', 
                   os.path.join(cwd, "smart_sample_apps"))

        fill_field('smart_server/settings.py', 'api_server_base_url', api_server_base_url)
        fill_field('smart_ui_server/settings.py', 'api_server_base_url', api_server_base_url)
        fill_field('smart_sample_apps/settings.py', 'app_server_base_url', app_server_base_url)
        fill_field('smart_sample_apps/settings.py', 'api_server_base_url', api_server_base_url)

        fill_field('smart_server/settings.py', 'chrome_consumer', chrome_consumer)
        fill_field('smart_server/settings.py', 'chrome_secret', chrome_secret)
        fill_field('smart_server/settings.py', 'db_password', db_password)

        fill_field('smart_ui_server/settings.py', 'chrome_consumer', chrome_consumer)
        fill_field('smart_ui_server/settings.py', 'chrome_secret', chrome_secret)
        fill_field('smart_ui_server/settings.py', 'db_password', db_password)
        
        fill_field('smart_sample_apps/settings.py', 'db_password', db_password)
        
        fill_field('smart_server/settings.py', 'django_secret_key', ''.join([choice(PASSWORD_LETTERBANK) for i in range(8)]))
        fill_field('smart_ui_server/settings.py', 'django_secret_key', ''.join([choice(PASSWORD_LETTERBANK) for i in range(8)]))
        fill_field('smart_sample_apps/settings.py', 'django_secret_key', ''.join([choice(PASSWORD_LETTERBANK) for i in range(8)]))

        fill_field('smart_server/settings.py', 'ui_server_base_url', ui_server_base_url)
        
        fill_field('smart_ui_server/settings.py', 'pretty_name_value', 'Reference EMR')

        if standalone_mode=="no":
            print "nostandalone"
            fill_field('smart_server/settings.py', 'use_proxy', 'True')
            fill_field('smart_server/settings.py', 'proxy_user_email', proxy_user)
            fill_field('smart_server/settings.py', 'proxy_base', proxy_base)

        else: 
            print "yes standalone"
            fill_field('smart_server/settings.py', 'use_proxy', 'False')

        fill_field('smart_server/settings.py', 'triplestore_engine', 'sesame')

        fill_field('smart_server/settings.py', 'triplestore_endpoint',
                'http://localhost:8080/openrdf-sesame/repositories/record_rdf')

    if args.run_app_server or args.run_api_servers:
        args.kill_servers = True
        server_settings = imp.load_source("settings", "smart_server/settings.py")
        app_settings = imp.load_source("settings", "smart_sample_apps/settings.py")
        app_server = app_settings.SMART_APP_SERVER_BASE
        api_server = server_settings.SITE_URL_PREFIX
        ui_server = server_settings.SMART_UI_SERVER_LOCATION

    if args.kill_servers:
        call_command("ps ax | "+
                     "grep -i 'python' | "+
                     "grep -i 'manage.py' | "+
                     "egrep  -o '^[ 0-9]+' | "+
                     "xargs -t  kill", failure_okay=True)
                     
    if args.generate_sample_data:
        call_command("cd smart_sample_patients/bin && " + 
                     "rm -rf ../generated-data/*.xml && " + 
                     "python generate.py --write ../generated-data &&" + 
                     "python generate-vitals-patient.py ../generated-data/99912345.xml &&" +
                     "cd ../..", print_output=True)

    if args.run_app_server:
        port = get_port(app_server)
        print "port:", port
        call_command("cd smart_sample_apps && python manage.py runconcurrentserver %s 0.0.0.0:%s &"%(reloadflag, port), 
                     print_output=True)
        call_command("sleep 2")

        print "App Server running."

    if args.reset_servers:
        print "Resetting the SMART server..."
        print "Note: Enter the SMART databse password when prompted (2 times)."
        print "      It is 'smart' by default."
        call_command("cd smart_server && "+
                     "sh ./reset.sh && "+
                     "cd ../..", print_output=True)
        
        print "Resetting the SMART UI server..."
        print "Note: Enter the SMART databse password when prompted (2 times)."
        print "      It is 'smart' by default."
        call_command("cd smart_ui_server && "+
                     "sh ./reset.sh &&"+
                     "cd ../..", print_output=True)


    if args.load_sample_data:
        call_command("cd smart_server && " + 
                     "PYTHONPATH=.:.. DJANGO_SETTINGS_MODULE=settings "+
                     "python load_tools/load_one_patient.py  " + 
                     "../smart_sample_patients/generated-data/* ../smart_sample_patients/deidentified-patients/*  && "
                     "cd ..", print_output=True)

    if args.create_user:
        print "Configuring a user ..."

        given_name = get_input("Given Name", "Demo")
        family_name = get_input("Family Name", "User")
        email = get_input("Email", "demouser@smartplatforms.org")
        password = get_input("Password", "password")

        call_command("cd smart_server && " + 
                     "PYTHONPATH=.:.. DJANGO_SETTINGS_MODULE=settings "+
                     "python load_tools/create_user.py  " + 
                     given_name + " " + 
                     family_name + " " + 
                     email + " " + 
                     password + " && " 
                     "cd ..", print_output=True)

    if args.run_api_servers:

        port = get_port(api_server)
        print "port:", port
        call_command("cd smart_server && python manage.py runconcurrentserver %s 0.0.0.0:%s &"%(reloadflag, port), 
                     print_output=True)
        print "API Servers running."

        port = get_port(ui_server)
        print "port:", port
        call_command("cd smart_ui_server && python manage.py runconcurrentserver %s 0.0.0.0:%s &"%(reloadflag, port), 
                     print_output=True)
        call_command("sleep 2")

def get_port(url):
    server = urlparse.urlparse(url)
    port = server.port
    if not port: 
        port  = (server.scheme == "http" and 80 or server.scheme == "https" and 443)
    return port

def call_command(command, print_output=False, failure_okay = False):
    print command
    ret = ""
    if print_output: 
        ret = os.system(command)
        assert failure_okay or os.WEXITSTATUS(ret) == 0, "Subcommand failed. Aborting."
        
    else: 
        try:
            ret = subprocess.check_output(command, shell=True,
                                   stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            if not failure_okay:
                assert False, "Subcommand failed.  Aborting."

    return ret

if __name__ == "__main__":
    main()
