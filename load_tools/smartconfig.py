#!/usr/bin/env python
import sys
import os
import re
import imp
import subprocess
import logging
import optparse
import string
import urlparse
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
    c = "sed -i -e's/%s/%s/' %s" % (n, v, t)
    o, s = call_command(c)
    print o, s
    return o

def fill_field(t, n, v):
    return do_sed(t, "{{%s}}"%n, v)

def main():
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage)

    parser.add_option("-a", "--all-steps", dest="all_steps",
                    action="store_true",
                    default=False,
                    help="All steps: clone, generate settings, "+
                      "kill running servers, generate sample data, "+
                      "run app server, reset api server, "+
                      "load sample data, run api servers")

    parser.add_option("-g", "--clone-git-repositories", dest="clone_git",
                    action="store_true",
                    default=False,
                    help="Clone git repositories")

    parser.add_option("-d", "--development-branch", dest="branch_dev",
                    action="store_true",
                    default=False,
                    help="Use development branch (in conjunction with -g)")

    parser.add_option("-s", "--generate-settings-files", dest="generate_settings",
                    action="store_true",
                    default=False,
                    help="Generate settings files")

    parser.add_option("-p", "--generate-sample-data", dest="generate_sample_data",
                    action="store_true",
                    default=False,
                    help="Generate sample patient data")

    parser.add_option("-k", "--kill-servers", dest="kill_servers",
                    action="store_true",
                    default=False,
                      help="Kill all currently-running django development servers")

    parser.add_option("-v", "--run-app-server", dest="run_app_server",
                    action="store_true",
                    default=False,
                    help="Run servers")

    parser.add_option("-r", "--reset-api-server", dest="reset_servers",
                    action="store_true",
                    default=False,
                    help="Reset API server")

    parser.add_option("-l", "--load-sample-data", dest="load_sample_data",
                    action="store_true",
                    default=False,
                    help="Load sample data into DB")

    parser.add_option("-u", "--run-api-servers", dest="run_api_servers",
                    action="store_true",
                    default=False,
                    help="Run servers")

    options, args = parser.parse_args()

    if not options.all_steps and not ( 
        options.clone_git or
        options.generate_settings or
        options.generate_sample_data or
        options.load_sample_data or
        options.kill_servers or
        options.reset_servers or
        options.run_app_server or 
        options.run_api_servers):
        
        parser.print_help()
        sys.exit(1)

    if options.all_steps:
        options.clone_git = True
        options.generate_settings  = True
        options.generate_sample_data  = True
        options.load_sample_data  = True
        options.kill_servers = True
        options.run_app_server = True
        options.reset_servers  = True
        options.run_api_servers = True


    if options.clone_git:

        print "Cloning (4) SMART git repositories..."
        call_command("git clone --recursive https://github.com/chb/smart_server.git", 
                     print_output=True)

        call_command("git clone --recursive https://github.com/chb/smart_ui_server.git", 
                     print_output=True)

        call_command("git clone --recursive https://github.com/chb/smart_sample_apps.git", 
                     print_output=True)

        call_command("git clone --recursive https://github.com/chb/smart_sample_patients.git", 
                     print_output=True)

        if options.branch_dev:
            call_command("cd smart_server; git checkout dev; cd ..")
            call_command("cd smart_ui_server; git checkout dev; cd ..")
            call_command("cd smart_sample_patients; git checkout dev; cd ..")
            call_command("cd smart_sample_apps; git checkout dev; cd ..")

        call_command("cd smart_server; git submodule init && git submodule update; cd ..", print_output=True)
        call_command("cd smart_ui_server; git submodule init && git submodule update; cd ..", print_output=True)
        call_command("cd smart_sample_patients; git submodule init && git submodule update; cd ..", print_output=True)
        call_command("cd smart_sample_apps; git submodule init && git submodule update; cd ..", print_output=True)


    if options.generate_settings:
        print "Configuring SMART server settings..."

        api_server_base_url = get_input("SMART API Server", "http://localhost:7000")
        
        chrome_consumer = get_input("Chrome App Consumer ID", "chrome")
        
        chrome_secret = get_input("Chrome App Consumer secret",  
                                  ''.join([choice(PASSWORD_LETTERBANK) for i in range(8)]))

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
        
        o, s = call_command("cp smart_server/settings.py.default smart_server/settings.py")

        o, s = call_command("cp smart_server/bootstrap_helpers/application_list.json.default " + 
                            "smart_server/bootstrap_helpers/application_list.json ")

        do_sed('smart_server/bootstrap_helpers/application_list.json', 
                   'http:\/\/localhost:8001',
                   app_server_base_url)


        o, s = call_command("cp smart_ui_server/settings.py.default smart_ui_server/settings.py")
        o, s = call_command("cp smart_sample_apps/settings.py.default smart_sample_apps/settings.py")

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


        fill_field('smart_ui_server/settings.py', 'chrome_consumer', chrome_consumer)
        fill_field('smart_ui_server/settings.py', 'chrome_secret', chrome_secret)

        fill_field('smart_server/settings.py', 'ui_server_base_url', ui_server_base_url)

        if standalone_mode=="no":
            print "nostandalone"
            fill_field('smart_server/settings.py', 'use_proxy', 'True')
            fill_field('smart_server/settings.py', 'proxy_user_email', proxy_user)
            fill_field('smart_server/settings.py', 'proxy_base', proxy_base)

        else: 
            print "yes standalone"
            fill_field('smart_server/settings.py', 'use_proxy', 'False')

    if options.generate_sample_data:

        call_command("cd smart_sample_patients/bin; " + 
                     "rm -rf ../generated_data; " + 
                     "mkdir ../generated_data; " + 
                     "python generate.py --write ../generated_data;" + 
                     "cd ../..;", print_output=True)

    if options.run_app_server or options.run_api_servers:
        options.kill_servers = True
        server_settings = imp.load_source("settings", "smart_server/settings.py")
        app_settings = imp.load_source("settings", "smart_sample_apps/settings.py")


        app_server = app_settings.SMART_APP_SERVER_BASE
        api_server = server_settings.SITE_URL_PREFIX
        ui_server = server_settings.SMART_UI_SERVER_LOCATION



    if options.kill_servers:
        call_command("ps -ah | "+
                     "grep -i 'python manage.py' | "+
                     "egrep  -o '^\ *[0\-9]+' | "+
                     "xargs -i  kill '{}'")

    if options.run_app_server:
        port = get_port(app_server)
        print "port:", port
        call_command("cd smart_sample_apps && python manage.py runconcurrentserver 0.0.0.0:%s --noreload &"%port, 
                     print_output=True)

        print "App Server running."

    if options.reset_servers:
        call_command("cd smart_server && "+
                     "sh ./reset.sh;"+
                     "cd ../..;", print_output=True)


    if options.load_sample_data:
        call_command("cd smart_server; " + 
                     "PYTHONPATH=.:.. DJANGO_SETTINGS_MODULE=settings "+
                     "python load_tools/load_one_patient.py  " + 
                     "../smart_sample_patients/generated_data/* ;"
                     "cd ..;", print_output=True)


    if options.run_api_servers:
        port = get_port(ui_server)
        print "port:", port
        call_command("cd smart_ui_server; python manage.py runconcurrentserver 0.0.0.0:%s --noreload &"%port, 
                     print_output=True)

        port = get_port(api_server)
        print "port:", port
        call_command("cd smart_server; python manage.py runserver 0.0.0.0:%s --noreload &"%port, 
                     print_output=True)

        print "API Servers running."

def get_port(url):
    server = urlparse.urlparse(url)
    port = server.port
    if not port: 
        port  = (server.scheme == "http" and 80 or server.scheme == "https" and 443)
    return port

def call_command(command, print_output=False):
    print command

    if print_output: 
        out = sys.stdout
        ret = os.system(command)
        
    else: 
        out = subprocess.PIPE
        process = subprocess.Popen(command, shell=True,
                                   stdout=out,
                                   stderr=subprocess.PIPE)
        ret = process.communicate()    
    return ret

if __name__ == "__main__":
    main()
