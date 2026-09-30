# ADDITION 1 PROGRAM

Utilising the source code below:
```asm
; Assemble the file   : nasm -f elf32 hello_world_32.asm -o hello_world_32.o
; Link:                 ld -m elf_i386 hello_world_32.o -o hello32 
; Run/Execute:          ./hello32

section .data
    num1 db 120   ; 01111000b
    num2 db 10    ; 00001010b
    result db 0   ; 10000010b

section .text
    global _start

_start:

    ; add [num1], [num2]

    mov al, [num1]
    add al, [num2]       ; al = num1 + num2        10000010
    mov [result], al

n_break:
    mov eax, 1
    xor ebx, ebx
    int 0x80
```

We can be able to debug and analyze:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    al,ds:0x804a000
   0x08049005 <+5>:     add    al,BYTE PTR ds:0x804a001
   0x0804900b <+11>:    mov    ds:0x804a002,al
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/bd 0x804a000
0x804a000 <num1>:       120
pwndbg> x/bd 0x804a001
0x804a001 <num2>:       10
```

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b *_start
Breakpoint 1 at 0x8049000: file ./add/add1.asm, line 17.
pwndbg> b *n_break
Breakpoint 2 at 0x8049010: file ./add/add1.asm, line 22.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/add/add1 
Downloading separate debug info for system-supplied DSO at 0xf7ffc000
Download failed: Invalid argument.  Continuing without separate debug info for system-supplied DSO at 0xf7ffc000.

...
In file: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/add/add1.asm:17
   11     global _start
   12 
   13 _start:
   14 
   15     ; add [num1], [num2]
   16 
 ► 17     mov al, [num1]
   18     add al, [num2]       ; al = num1 + num2        10000010
   19     mov [result], al
   20 
   21 n_break:
   22     mov eax, 1
   23     xor ebx, ebx
   24     int 0x80
...
──────────────────────────────────────────────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────────────
 ► 0 0x8049000 _start
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> 
```
- Investigate
```bash
pwndbg> info registers eflags
eflags         0x202               [ IF ]
pwndbg> n
pwndbg> n

...
────────────────────────────────────────────────────────────────────────────────────────[ SOURCE (CODE) ]─────────────────────────────────────────────────────────────────────────────────────────
In file: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/add/add1.asm:19
   11     global _start
   12 
   13 _start:
   14 
   15     ; add [num1], [num2]
   16 
   17     mov al, [num1]
   18     add al, [num2]       ; al = num1 + num2        10000010
 ► 19     mov [result], al
   20 

pwndbg> info reg eflags
eflags         0xa96               [ PF AF SF IF OF ]
pwndbg> c

...
   21 n_break:
 ► 22     mov eax, 1
   23     xor ebx, ebx
   24     int 0x80
...
pwndbg> info reg eflags
eflags         0xa96               [ PF AF SF IF OF ]
pwndbg> 
```

From the program, the following flags are set:
- PF (Parity Flag) - 2-1 bit in the result hence even number of 1 bits in the accumulator
- AF (Auxilliary Flag) -there is a carry from the lower nibble to the upper nibble
- SF (Sign Bit Flag) - the most significant bit is set (1)
- IF (Interrupt Flag) - controls whether the CPU responds to maskable hardware interrupts.
- OF (Overflow Flag) - the result overflowed past the required +127 limit (+130)

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0and IF is set to 1 for normal user processes.