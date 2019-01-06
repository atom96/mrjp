global top_printString
global top_printInt
global top_strConcat

extern printf
extern _str_concat

section .data

strfmt db '%s',0xa,0
strfmt2 db '%d',0xa,0

section .text

top_printString:
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



top_printInt:
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

mov rdi, strfmt2
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


top_strConcat:
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
