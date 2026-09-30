# ADDITION 2 PROGRAM

Utilising the source code below:
```bash
; add16.asm
section .data
    num1 dw 32000
    num2 dw 500
    result dw 0

section .text
    global _start

_start:
    mov ax, [num1]
    add ax, [num2]       ; AX = num1 + num2
    mov [result], ax

    mov eax, 1
    xor ebx, ebx   ; zero flag set
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     add    ax,WORD PTR ds:0x804a002
   0x0804900d <+13>:    mov    ds:0x804a004,ax
   0x08049013 <+19>:    mov    eax,0x1
   0x08049018 <+24>:    xor    ebx,ebx
   0x0804901a <+26>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <num1>:       32000
pwndbg> x/hd 0x804a002
0x804a002 <num2>:       500
pwndbg> x/hd 0x804a004
0x804a004 <result>:     0
pwndbg> 
```

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./add/add2.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/add/add2 

Breakpoint 1, _start () at ./add/add2.asm:11
...
   10 _start:
 ► 11     mov ax, [num1]
   12     add ax, [num2]       ; AX = num1 + num2
   13     mov [result], ax
   14 
   15     mov eax, 1
   16     xor ebx, ebx   ; zero flag set
   17     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
...


pwndbg> ni 3

   0x8048ffc                add    byte ptr [eax], al
   0x8048ffe                add    byte ptr [eax], al
b+ 0x8049000 <_start>       mov    ax, word ptr [num1]       AX, [num1] => 0x7d00
   0x8049006 <_start+6>     add    ax, word ptr [num2]       AX => 0x7ef4 (0x7d00 + 0x1f4)
   0x804900d <_start+13>    mov    word ptr [result], ax     [result] <= 0x7ef4
 ► 0x8049013 <_start+19>    mov    eax, 1                    EAX => 1
   0x8049018 <_start+24>    xor    ebx, ebx                  EBX => 0
   0x804901a <_start+26>    int    0x80 <SYS_exit>
   0x804901c                add    byte ptr [eax], al
   0x804901e                add    byte ptr [eax], al
   0x8049020                add    byte ptr [eax], al
```

- Investigate flags
```bash
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
pwndbg> p $ax
$1 = 0x7ef4
pwndbg> p/d $ax
$2 = 32500
```

AX is a 2 byte register (16 bit), hence it supports 2^15 numbers (1 bit for sign bit), which are (-(2^15) to 2^15-1) = -32768 to 32767.

Our result `32500` falls between the range, there is no overflow (OF) and no sign bit set (SF). `32500` can be written as `1111110 11110100` which contains 5 number of 1s in the lower 8 bits which is odd.

Hence `IF` (Interrupt Flag) is the only flag set so far.

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```