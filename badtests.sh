
#set -e
nasm -f elf64 -F dwarf -g defaults.asm -o ctest/defaults.o

source venv/bin/activate


DIRS=(sttests/bad/semantic lattests/bad/ )


for DIR in ${DIRS[*]}; do

for d in $DIR/* ; do
    if [ ${d: -4} == ".lat" ]
    then
       echo checking $d
        y=${d%.lat}
        python grammar_test.py $d


       if [ $? -eq 0 ]; then
           echo 'error not found'
           exit 1
       fi


# do something txt-ish
    fi

done
done
