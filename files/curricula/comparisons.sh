#!/bin/bash

for d in ./files/curricula/*/ ; do
    # Strip the top 7 lines - i.e. the header
    #for f in $d/*; do
    #    sed '1,7d' $f
    #done
    for f1 in $d/*; do
        for f2 in $d/*; do
            echo "$f1 v $f2"
            diff $f1 $f2 
        done
    done
done