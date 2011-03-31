import os
import subprocess
from smart.lib.utils import url_request

def interpolated_postgres_load(source_file, interpolations, db, user):

    f = open(source_file).read()
    for (k,v) in interpolations.iteritems():
        f = f.replace("{{%s}}"%k, v)


    g = open("postgres_load_temp", "w")
    g.write(f)
    g.close()


    print "loading postgres data..."
    pr = subprocess.Popen("psql -U %s -f postgres_load_temp %s "%(user, db), shell=True, stdin=subprocess.PIPE)
    pr.communicate()

    os.remove("postgres_load_temp")
