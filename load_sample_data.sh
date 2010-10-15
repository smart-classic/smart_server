#!/bin/bash
for i in records/*/*/*;   do  wget --post-file=$i  http://localhost:7000/${i%/*}/;  done
