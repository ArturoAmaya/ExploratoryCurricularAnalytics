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
echo "" > ./DEI_major.txt
echo "" > ./DEI_missing.txt
# Loop through the curricula folder, only stopping at folders
for folder in ./files/curricula/*/ ; do
    echo -e "$folder" >> ./files/DEI_finder.txt
    # for each folder, loop through all the files.
    for file in $folder/* ; do
        # Find the line number (and line content) of the line with DEI in it. Format is Line#:CourseID,DEI,[...]
        var=$(grep -n DEI $file)
        # Remove everything after the first comma. %% deletes longest matching pattern from the end. 
        var=${var%%,*}
        # Find where the transition from curricula to degree plan is.
        var2=$(grep -n "Additional Courses" $file)
        #Trim to just the line number
        var2=${var2%%:*}
        #Save that data
        echo -e "\t $var in $file" >> ./files/DEI_finder.txt
        echo -e "\t $var2 for additional course in $file" >> ./files/DEI_finder.txt
        var=${var%%:*}
        # If the string isn't empty, if the lin enumber for additional courses is greater than the DEI line number
        # then the DEI is listed as a major course.
        # Otherwise, only flag that there's no DEI if the file is not a curriculum.
        if [ ! "$var" = "" ]; then
            if ((var2 > var)); then
                echo "UHOH in $file, the DEI is in the major courses list" >> DEI_major.txt
            fi
        else 
            # check if it's a curriculum
            temp=${file##*_}
            if [ ! "$temp" = "curriculum.csv" ]; then
                echo -e "There's no DEI in $file" >> DEI_missing.txt
            fi
        fi
    done
    echo "" >> ./files/DEI_finder.txt
done