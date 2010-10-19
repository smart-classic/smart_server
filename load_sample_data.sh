#!/bin/bash

for i in `find records/ -name data.rdf | sort -u`; 
do  
    url="http://localhost:7000/${i%/*}/"
    [[ $i == *external_id* ]] &&  url="${url%/}"
    wget --post-file=$i  $url;  
done