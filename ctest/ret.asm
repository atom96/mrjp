global top_main
extern top_printString
extern top_printInt
extern strConcat
extern malloc
section .data

section .text
top_main:
push rbp
mov rbp, rsp
add rsp, 0
push rax
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
add rsp, 8
mov eax, 50
push rax
mov eax, 1
push rax
call top_fromTo
mov rsp, r12
pop r12
push rax
call top_length
mov rsp, r12
pop r12
push rax
call top_printInt
mov rsp, r12
pop r12
pop rax
push rax
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
add rsp, 8
mov eax, 100
push rax
mov eax, 1
push rax
call top_fromTo
mov rsp, r12
pop r12
push rax
call top_length2
mov rsp, r12
pop r12
push rax
call top_printInt
mov rsp, r12
pop r12
pop rax
mov eax, 0
mov rsp, rbp
pop rbp
ret
top_head:
push rbp
mov rbp, rsp
add rsp, 0
mov rax, QWORD [rbp+16]
mov eax, DWORD [rax+0]
mov rsp, rbp
pop rbp
ret
top_cons:
push rbp
mov rbp, rsp
add rsp, -8
push rax
xor rax, rax
mov QWORD [rbp-8], rax
pop rax
push rax
push rbx
lea rax, [rbp-8]
push rax
push rdi
mov rdi, 16
call malloc
mov QWORD [rax + 0], 0
mov QWORD [rax + 8], 0
pop rdi
mov rbx, rax
pop rax
mov [rax], rbx
pop rbx
pop rax
push rax
push rbx
mov rax, QWORD [rbp-8]
lea rax,  [rax+0]
mov ebx, DWORD [rbp+16]
mov [rax], ebx
pop rbx
pop rax
push rax
push rbx
mov rax, QWORD [rbp-8]
lea rax,  [rax+8]
mov rbx, QWORD [rbp+24]
mov [rax], rbx
pop rbx
pop rax
mov rax, QWORD [rbp-8]
mov rsp, rbp
pop rbp
ret
top_length:
push rbp
mov rbp, rsp
add rsp, 0
push rax
push rbx
mov rax, QWORD [rbp+16]
xor rbx, rbx
cmp eax, ebx
pop rbx
pop rax
je L1
jmp L2
L1:
mov eax, 0
mov rsp, rbp
pop rbp
ret
jmp L3
L2:
push rbx
mov eax, 1
push rax
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
mov rax, QWORD [rbp+16]
mov rax, QWORD [rax+8]
push rax
call top_length
mov rsp, r12
pop r12
mov ebx, eax
pop rax
add eax, ebx
pop rbx
mov rsp, rbp
pop rbp
ret
L3:
top_fromTo:
push rbp
mov rbp, rsp
add rsp, 0
push rax
push rbx
mov eax, DWORD [rbp+16]
mov ebx, DWORD [rbp+24]
cmp eax, ebx
pop rbx
pop rax
jg L4
jmp L5
L4:
xor rax, rax
mov rsp, rbp
pop rbp
ret
jmp L6
L5:
push rax
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
add rsp, 8
mov eax, DWORD [rbp+24]
push rax
push rbx
mov eax, DWORD [rbp+16]
mov ebx, 1
add eax, ebx
pop rbx
push rax
call top_fromTo
mov rsp, r12
pop r12
mov QWORD [rbp-8], rax
pop rax
push r12
mov r12, rsp
and rsp, 0xFFFFFFFFFFFF0000
add rsp, 8
mov rax, QWORD [rbp-8]
push rax
mov eax, DWORD [rbp+16]
push rax
call top_cons
mov rsp, r12
pop r12
mov rsp, rbp
pop rbp
ret
L6:
top_length2:
push rbp
mov rbp, rsp
add rsp, -4
push rax
mov eax, 0
mov DWORD [rbp-4], eax
pop rax
jmp L8
L7:
push rax
lea rax, [rbp-4]
inc DWORD [rax]
pop rax
push rax
push rbx
lea rax, [rbp+16]
mov rbx, QWORD [rbp+16]
mov rbx, QWORD [rbx+8]
mov [rax], rbx
pop rbx
pop rax
L8:
push rax
push rbx
mov rax, QWORD [rbp+16]
xor rbx, rbx
cmp eax, ebx
pop rbx
pop rax
jne L7
jmp L9
L9:
mov eax, DWORD [rbp-4]
mov rsp, rbp
pop rbp
ret

