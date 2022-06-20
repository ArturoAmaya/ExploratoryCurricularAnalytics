#!/bin/bash
#for d in ./files/curricula/*/ ; do
    # Strip the top 7 lines - i.e. the header
    #for f in $d/*; do
    #    sed '1,7d' $f
    #done
#    for f1 in $d/*; do
#        for f2 in $d/*; do
#            echo "$f1 v $f2"
#            diff $f1 $f2 
#        done
#    done
#done
echo "" > ./files/DEI_finder.txt
for folder in ./files/curricula/*/ ; do
    echo -e "$folder" >> ./files/DEI_finder.txt
    for file in $folder/* ; do
        var=$(grep -n DEI $file)
        var=${var%%,*}
        var2=$(grep -n "Additional Courses" $file)
        var2=${var2%%:*}
        echo -e "\t $var in $file" >> ./files/DEI_finder.txt
        echo -e "\t $var2 for additional course in $file" >> ./files/DEI_finder.txt
        var=${var%%:*}
        if [ ! "$var" = "" ]; then
            if ((var2 > var)); then
                echo "UHOH in $file, the DEI is in the major courses list"
            fi
        else 
            # check if it's a curriculum
            temp=${file##*_}
            if [ ! "$temp" = "curriculum.csv" ]; then
                echo -e "There\'s no DEI in $file"
            fi
        fi
    done
    echo "" >> ./files/DEI_finder.txt
done