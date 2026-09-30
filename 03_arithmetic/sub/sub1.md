# SUBTRACTION 1 PROGRAM

Utilising the source code below:
```asm
; sub8.asm
section .data
    num1 db 50   ; 00110010
    num2 db 80   ; 01010000
    result db 0

section .text
    global _start

_start:
    mov al, [num1]
    sub al, [num2]       ; al = 50 - 80
    mov [result], al   ;

    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    al,ds:0x804a000
   0x08049005 <+5>:     sub    al,BYTE PTR ds:0x804a001
   0x0804900b <+11>:    mov    ds:0x804a002,al
   0x08049010 <+16>:    mov    eax,0x1
   0x08049015 <+21>:    xor    ebx,ebx
   0x08049017 <+23>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/bd 0x804a000
0x804a000 <num1>:       50
pwndbg> x/bd 0x804a001
0x804a001 <num2>:       80
pwndbg> x/bd 0x804a002
0x804a002 <result>:     0
pwndbg> 
```

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./sub/sub1.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/sub/sub1 

Breakpoint 1, _start () at ./sub/sub1.asm:11
...
   10 _start:
 ► 11     mov al, [num1]
   12     sub al, [num2]       ; al = 50 - 80
   13     mov [result], al   ;
   14 
   15     mov eax, 1
   16     xor ebx, ebx
   17     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `sub` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900b <_start+11>    mov    byte ptr [result], al
...
pwndbg> p/x $al
$1 = 0xe2
pwndbg> p/t $al
$2 = 11100010
pwndbg> p/d $al
$3 = -30
pwndbg> p/u $al
$4 = 226
pwndbg> info reg eflags
eflags         0x287               [ CF PF SF IF ]
pwndbg>
```

The subtraction `50 - 80` is done in binary as:
```
  00110010   (50)
- 01010000   (80)
= 11100010   (0xE2)
```

`11100010` is `226` if read as an unsigned number and `-30` if read as a signed (two's complement) number, which is the correct answer for `50 - 80`.

From the program, the following flags are set:
- CF (Carry Flag) - on a subtraction it acts as a borrow. `50` is smaller than `80` as unsigned numbers, so we had to borrow from beyond the 8th bit
- PF (Parity Flag) - 4 number of 1s in the lower 8 bits of the result (`11100010`), hence an even number of 1 bits
- SF (Sign Bit Flag) - the most significant bit is set (1), the result is negative
- IF (Interrupt Flag) - controls whether the CPU responds to maskable hardware interrupts, set to 1 for normal user processes

The following flags are **not** set:
- ZF (Zero Flag) - the result is not `0`
- AF (Auxilliary Flag) - no borrow from the upper nibble to the lower nibble (`0x2 - 0x0` needs no borrow)
- OF (Overflow Flag) - as a signed operation `50 - 80 = -30` is within `-128` to `127`. So CF flags the unsigned overflow (borrow) while OF stays clear for the signed one.

- Store the result in memory
```bash
pwndbg> ni
pwndbg> x/bd &result
0x804a002 <result>:     -30
pwndbg> x/bu &result
0x804a002 <result>:     226
```

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```
