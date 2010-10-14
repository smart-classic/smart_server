for i in records/*; do  wget --post-file=$i/demographics/001  http://localhost:7000/$i/demographics/; done
for i in records/*/problems/*;   do  wget --post-file=$i  http://localhost:7000/${i%/*}/;  done
for i in records/*/medications/*;   do  wget --post-file=$i  http://localhost:7000/${i%/*}/;  done
