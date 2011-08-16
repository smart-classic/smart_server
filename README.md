#The SMArt reference EMR documentation is rapidly evolving.  If something in this document looks strange, confusing, or wrong, please ask about it:
###http://groups.google.com/group/smart-app-developers

# Repositories 
These instructions apply to each of three github repositories that you'll need in order to run the SMArt Reference EMR in your own environment:

* https://github.com/chb/smart_server.git

* https://github.com/chb/smart_ui_server.git

* https://github.com/chb/smart_sample_apps.git

* https://github.com/chb/smart_sample_patients.git

# System setup

* Recent Linux installation (Kernel 2.6+).  We recommend an up-to-date version of Ubuntu, and these instructions are written from that perspective.
* Note: These instructions have been updated for Ubuntu 11.4.
* Note: We recommend you do this by sudo'ing from a non-root user.  If you would like to do this as root make sure you create at least one non-root user with `useradd -m {USER}` otherwise the default locale will not be set.  This issue is most common on a new OS build.

* Python 2.7 with package <tt>psycopg2</tt> and <tt>libxslt1</tt>
<pre>
    sudo apt-get install python-psycopg2 python-libxslt1 python-m2crypto python-simplejson python-argparse python-setuptools python-pyparsing

    sudo easy_install -U "rdflib>=3.0.0"  rdfextras
</pre>

* Django 1.1
<pre>
    sudo apt-get install python-django
</pre>

* PostgreSQL 8.3+
<pre>
     sudo apt-get install postgresql
</pre>

# Setup Database

You'll have the easiest time naming your database <tt>smart</tt>

* There are two ways to authenticate to PostgreSQL: use your Unix credentials, or use a separate username and password. We strongly recommend the latter, and our instructions are tailored appropriately. If you know how to use PostgreSQL and want to use Unix-logins, go for it, just remember that when you use Apache, it will usually try to log in using its username, <tt>www-data</tt>.

* in <tt>/etc/postgresql/8.4/main/pg_hba.conf</tt>, find the line that reads:

  `local     all     all        ident`

This should be the second uncommented line in your default config. Change <tt>ident</tt> to <tt>md5</tt>:

  `local     all     all        md5`

* You will need to restart PostgreSQL:
<pre>
   sudo service postgresql restart
</pre>

* Create a PostgreSQL user for your SMArt service, e.g. "smart" and setup a password
 <pre>
 sudo su - postgres
 createuser --superuser smart
 psql
 postgres=# \password smart
 postgres=# \q
 </pre>

* Create the Databases and make the smart user their owner.
 <pre>
 createdb -O smart smart
 createdb -O smart rxnorm
 exit
 </pre>

# Install openrdf-sesame (and tomcat)  

* get Tomcat and OpenRDF-Sesame:
<pre>
 sudo apt-get install tomcat6
 wget http://downloads.sourceforge.net/project/sesame/Sesame%202/2.4.0/openrdf-sesame-2.4.0-sdk.tar.gz
</pre>

* install OpenRDF Sesame as a Tomcat web application
<pre>
 tar -xzvf openrdf-sesame-2.4.0-sdk.tar.gz
 sudo mkdir /usr/share/tomcat6/.aduna
 sudo chown tomcat6.tomcat6 /usr/share/tomcat6/.aduna/
 sudo cp -r openrdf-sesame-2.4.0/war/* /var/lib/tomcat6/webapps/
</pre>

* restart Tomcat (optional since autoDeploy is typically enabled in Tomcat by default)
<pre>
 sudo service tomcat6 restart
</pre>

* check that Tomcat and OpenRDF Sesame are running by hitting <tt>http://localhost:8080/openrdf-sesame/</tt>. You should see the main OpenRDF status page.

The OpenRDF store doesn't support access control. You will probably want to limit access to just localhost.
To limit servlet access to localhost, make two tomcat configuration changes:

<pre>
    /var/lib/tomcat6/conf/context.xml
    &lt;Context&gt;
    +  &lt;Valve className="org.apache.catalina.valves.RemoteHostValve" allow="localhost"/&gt;

    /var/lib/tomcat6/conf/server.xml
    &lt;Connector port="8080" protocol="HTTP/1.1"
    +          enableLookups="true"
</pre>

You'll need to restart Tomcat again if you make these changes

# Download, Install, and Configure SMArt Backend Server 

* Install GIT
<pre>
     sudo apt-get install git
</pre>

* get the code
 <pre>
 git clone https://github.com/chb/smart_server.git
 cd smart_server
 git submodule init
 git submodule update
 </pre>

* copy <tt>settings.py.default</tt> to <tt>settings.py</tt> and update it:
    * set <tt>DATABASE_USER</tt> to the username you chose, in this documentation <tt>smart</tt>, and set <tt>DATABASE_PASSWORD</tt> accordingly.		
    * set <tt>APP_HOME</tt> to the complete path to the location where you've installed <tt>smart_server</tt>, e.g. <tt>/web/smart_server</tt>
    * set <tt>SITE_URL_PREFIX</tt> to the URL where your server is running, including port number  e.g. <tt>http://localhost:7000</tt>
    * set <tt>SMART_UI_SERVER_LOCATION</tt> to the URL where your UI server will be running, including port number  e.g. <tt>http://localhost:7001</tt>

* copy <tt>bootstrap_helpers/application_list.json.default</tt> to <tt>bootstrap_helpers/application_list.json</tt> and customize to include the apps you want.

* update the database and repository settings in <tt>reset.sh</tt> (if you changed the default DB and repository endpoints in <tt>settings.py</tt>

* set things up (supplying the smart db password when prompted a few times)
 <pre>
 ./reset.sh
 </pre>

   NOTE: On the first run of <tt>reset.sh</tt>, you will also see some 500s. Don't worry about them.  When the reset process completes, you should see:

   <pre>
   ...
   No fixtures found.
   </pre>

   This is normal -- nothing has gone wrong.
   
   IMPORTANT: if you've enabled apps that are part of the sample apps below, you should <em>wait</em> to run <tt>reset.sh</tt> until you've got the sample apps server running. The SMArt Reference EMR attempts to download the apps' manifest files, and if they're not available over HTTP, <tt>reset.sh</tt> won't complete successfully. If you mistakenly run <tt>reset.sh</tt> before setting up the SMArt Sample Apps, don't worry, just set up the SMArt Sample Apps server, and run <tt>reset.sh</tt> again.

# Download, Install, and Configure SMArt UI Server

* get the code

 <pre>
 git clone https://github.com/chb/smart_ui_server.git
 cd smart_ui_server
 git submodule init
 git submodule update
 </pre>

* copy <tt>settings.py.default</tt> to <tt>settings.py</tt> and update:
    * set <tt>SMART_UI_BASE</tt> to the complete path to the location where you've installed <tt>smart_ui_server</tt>, e.g. <tt>/web/smart_ui_server</tt>
    * set <tt>SMART_SERVER_LOCATION</tt>, <tt>CONSUMER_KEY</tt>, <tt>CONSUMER_SECRET</tt> appropriately to match the SMArt Server's location and chrome credentials. (Check your <tt>bootstrap.py</tt> within <tt>smart_server</tt> for those credentials. If you change them, you'll need to run <tt>reset.sh</tt> again on the SMArt server. If you never changed <tt>bootstrap.py</tt>, then your <tt>CONSUMER_KEY</tt> and <tt>CONSUMER_SECRET</tt> are both <tt>chrome</tt>, and you don't need to change their value in the UI server default settings file.)

# Download, Install, and Configure SMArt Sample Apps

* get the source code
 <pre>
 git clone https://github.com/chb/smart_sample_apps.git
 cd smart_sample_apps
 git submodule init
 git submodule update
</pre>

* copy settings.py.default to settings.py and update:
    * set <tt>APP_HOME</tt> to the complete path to the location where you've installed <tt>smart_sample_apps</tt>, e.g. <tt>/web/smart_sample_apps</tt>
    * set <tt>SMART_SERVER_PARAMS</tt> to point to the location of the SMArt Server. If you are running the SMArt server on <tt>localhost:7000</tt> as we suggest, there's no need to change anything.

# Generate Sample Patient Records and Load Them in the SMArt EMR

* get the source code and generate sample data
 <pre>
 git clone https://github.com/chb/smart_sample_patients.git
 cd smart_sample_patients/bin
 python generate.py --write ../test-data/
 </pre>

* Load into SMArt EMR
 <pre>
 cd /path/to/smart_server
 PYTHONPATH=.:.. DJANGO_SETTINGS_MODULE=settings /usr/bin/python \
   load_tools/load_one_patient.py \
   /path/to/smart_sample_patients/test-data/*
 </pre>
 
 Expect this to take a few minutes.

#Running the Development Servers

The Django development servers are easy to run at the prompt.

The backend server can run on localhost in the configuration given above:
<pre>
 cd /path/to/smart_server/
 nohup python manage.py runconcurrentserver 7000 > /dev/null 2>&1 &
</pre>

The UI server, if you want it accessible from another machine, needs to specify a hostname or IP address. If you want port 80, you need to be root of course. The mask "0.0.0.0" will allow all incoming connections:

<pre>
 cd /path/to/smart_ui_server/
 nohup python manage.py runconcurrentserver 0.0.0.0:7001 > /dev/null 2>&1 &
</pre>

And finally, the Sample Apps:

<pre>
 cd /path/to/smart_sample_apps/
 nohup python manage.py runconcurrentserver 0.0.0.0:8001 > /dev/null 2>&1 &
</pre>

* Note: In the above examples the console output is suppressed. If you are having trouble with the server, you may want to redirect the output to the console or a log file.

#The SMArt EMR is now at: http://localhost:7001/login
