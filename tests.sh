#set -e
nasm -f elf64 -F dwarf -g defaults.asm -o ctest/defaults.o

source venv/bin/activate

DIR=sttests/gr5/

DIRS=(sttests/good/basic sttests/good/virtual $DIR lattests/good/ lattests/extensions/struct lattests/extensions/objects*)


for DIR in ${DIRS[*]}; do

for d in $DIR/* ; do
    if [ ${d: -4} == ".lat" ]
    then
       echo checking $d
        y=${d%.lat}
        python grammar_test.py $d 

        nasm -f elf64 -F dwarf -g ${y}.s

        gcc -o ${y} ctest/testmain.c ctest/strcnc.c ${y}.o ctest/defaults.o

        INPT=${y}.input
        if [ ! -f $INPT ]; then
        
            INPT=/dev/null
        fi

        ./${y} < ${INPT} > ${y}.myout


        DIFF=$(diff ${y}.output ${y}.myout)

        if [ "$DIFF" != "" ] 
        then
		echo DIFF ${y} $DIFF
#                exit 1
#        else
#               echo "No diff" ${y}
	fi       

# do something txt-ish
    fi

done
done
