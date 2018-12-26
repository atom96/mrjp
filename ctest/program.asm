global program
global x
extern printString
extern strConcat
section .data

L3 db ' 42', 0
L2 db 'Hello', 0
L1 db 'xD', 0
section .text
program:
push rbp
mov rbp, rsp
add rsp, -4
push rax
mov eax, 5
mov DWORD [rbp-4], eax
pop rax
jmp L5
L4:
push rax
push rcx
mov rcx, rsp
and rsp, 0xFFFFFFFFFFFF0000
mov rax, L1
push rax
call printString
mov rsp, rcx
pop rcx
pop rax
dec DWORD [rbp-4]
L5:
push rax
push rbx
mov eax, DWORD [rbp-4]
mov ebx, 0
cmp eax, ebx
pop rbx
pop rax
jg L4
jmp L6
L6:
push rax
push rcx
mov rcx, rsp
and rsp, 0xFFFFFFFFFFFF0000
push rcx
mov rcx, rsp
and rsp, 0xFFFFFFFFFFFF0000
mov rax, L2
push rax
call x
mov rsp, rcx
pop rcx
push rax
call printString
mov rsp, rcx
pop rcx
pop rax
mov eax, 0
mov rsp, rbp
pop rbp
ret
x:
push rbp
mov rbp, rsp
add rsp, 0
push rcx
mov rcx, rsp
and rsp, 0xFFFFFFFFFFFF0000
add rsp, 8
mov rax, L3
push rax
mov rax, QWORD [rbp+16]
push rax
call strConcat
mov rsp, rcx
pop rcx
mov rsp, rbp
pop rbp
ret
