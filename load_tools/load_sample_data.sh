#!/bin/bash

for i in `find records/ -name data.rdf | sort -u`; 
do  
    url="http://localhost:7000/${i%/*}"
    wget -O /dev/null --post-file=$i  $url;  
done