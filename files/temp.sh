#!/bin/bash
#var="`grep -n "Additional Courses" ./files/curricula/AN26/AN26_FI.csv | grep -Eo '^[^:]+'`"
#echo "$var"

for d in ./files/curricula/*/ ; do
    for f in $d/*; do
        #sed '1,7d' $f
        echo "$f"
        var="`grep -n "Additional Courses" $f | grep -Eo '^[^:]+'`"
        echo "$var"
    done
done