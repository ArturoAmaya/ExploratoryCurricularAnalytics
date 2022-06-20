#!/bin/bash

majors=("AN26" "AN27" "AN28" "AN29" "AN30" "BE25" "BE27" "BE28" "BE29" "BI30" "BI31" "BI32" "BI34" "BI35" "BI37" "BI38" "CE25" "CR25" "CH25" "CH34" "CH35" "CH36" "CH38" "CN25" "CL25" "CG25" "CG29" "CG31" "CG32" "CG33" "CG34" "CG35" "CM26" "CS25" "CS26" "CS27" "DS25" "EC26" "EC27" "EC28" "EC37" "EN25" "EN26" "EN28" "EN30" "ED25" "ES25" "ES26" "ES27" "ES28" "ET25" "GH25" "GH26" "GS25" "GL25" "HS25" "HS26" "HS27" "HS28" "HI25" "IS25" "IS26" "IS27" "IS28" "IS29" "IS30" "IS31" "IS34" "IS36" "IT25" "JA25" "JS25" "LA25" "LA26" "LA27" "LN25" "LN29" "LN32" "LN33" "LN34" "LT33" "LT34" "LT36" "LT41" "MC25" "MC27" "MA27" "MA29" "MA30" "MA31" "MA32" "MA33" "MA34" "MA35" "MU25" "MU26" "MU27" "NA25" "PL25" "PY26" "PY28" "PY29" "PY30" "PY31" "PY32" "PY33" "PY34" "PS25" "PS26" "PS27" "PS28" "PS29" "PS30" "PS31" "PS32" "PS33" "PS34" "PC25" "PC26" "PC28" "PC29" "PC30" "PC31" "PC32" "PC33" "PC34" "PC35" "RE26" "RU26" "SE27" "SI29" "SI30" "SO25" "SO27" "SO28" "SO29" "SO30" "SO31" "SO32" "SO33" "PB25" "PB26" "PB27" "PB28" "PB29" "PB30" "PB31" "TH26" "TH27" "UN27" "UNHA" "UNPS" "UNSS" "US26" "US27" "VA26" "VA27" "VA28" "VA29" "VA30")
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
filepath="./files/curricula/${major}_curriculum"
for major in "${majors[@]}"; do
    echo "$major"
    `python output.py $major > ./files/curricula/"$major"/"$major"_curriculum.csv`
    `python output.py $major FI > ./files/curricula/"$major"/"$major"_FI.csv`
    `python output.py $major MU > ./files/curricula/"$major"/"$major"_MU.csv`
    `python output.py $major RE > ./files/curricula/"$major"/"$major"_RE.csv`
    `python output.py $major SI > ./files/curricula/"$major"/"$major"_SI.csv`
    `python output.py $major SN > ./files/curricula/"$major"/"$major"_SN.csv`
    `python output.py $major TH > ./files/curricula/"$major"/"$major"_TH.csv`
    `python output.py $major WA > ./files/curricula/"$major"/"$major"_WA.csv`
done
