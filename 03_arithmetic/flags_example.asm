; all_flags.asm
; Demonstrating CF, ZF, SF and OF

section .text
global _start

_start:

    ; --------------------------------
    ; ZERO FLAG
    ; --------------------------------

    mov al, 10
    sub al, 10

    ; Result = 0
    ; ZF = 1

    jz zero_detected

zero_detected:
    ; --------------------------------
    ; SIGN FLAG
    ; --------------------------------

    mov al, 5
    sub al, 10

    ; Result = -5
    ; SF = 1

    js sign_detected


sign_detected:
    ; --------------------------------
    ; CARRY FLAG
    ; --------------------------------

    mov al, 255
    add al, 1

    ; Result = 0
    ; CF = 1

    jc carry_detected


carry_detected:
    ; --------------------------------
    ; OVERFLOW FLAG
    ; --------------------------------

    mov al, 127
    add al, 1

    ; Signed result cannot fit
    ; OF = 1

    jo overflow_detected


overflow_detected:
    ; Exit
    mov eax, 60
    xor edi, edi
    syscall