set -e
nasm -f elf64 -F dwarf -g defaults.asm -o ctest/defaults.o

source venv/bin/activate
python grammar_test.py > ctest/program.asm

cd ctest

cat program.asm
echo

nasm -f elf64 -F dwarf -g program.asm
gcc -o test testmain.c strcnc.c program.o defaults.o
./test
