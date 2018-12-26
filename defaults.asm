global printString
global strConcat

extern printf
extern _str_concat

section .data

strfmt db '%s',0xa,0

section .text

printString:
push rbp
mov rbp, rsp

push RAX
push RCX
push RDX
push R8
push R9
push R10
push R11
push RDI
push RSI

mov rdi, strfmt
mov rsi, [rbp + 16]
mov rax, 0
call printf

pop RSI
pop RDI
pop R11
pop R10
pop R9
pop R8
pop RDX
pop RCX
pop RAX

mov rsp, rbp
pop rbp
ret


strConcat:
push rbp
mov rbp, rsp

push RCX
push RDX
push R8
push R9
push R10
push R11
push RDI
push RSI

mov rdi, [rbp + 16]
mov rsi, [rbp + 24]

call _str_concat

pop RSI
pop RDI
pop R11
pop R10
pop R9
pop R8
pop RDX
pop RCX

mov rsp, rbp
pop rbp
ret
