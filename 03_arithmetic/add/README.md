# ADDITION PROGRAMS

Three programs using `add` and `adc`. On an addition CF is the **unsigned** carry-out of the top bit, OF is the **signed** overflow (both operands have the same sign and the result has the opposite one), SF copies the top bit of the result, ZF is set when the result is 0, PF is set when the lowest byte has an even number of 1s, and AF is the carry from bit 3 into bit 4.

Each program was assembled with `nasm -f elf32`, linked with `ld -m elf_i386` (see [the build notes](../readme.md)) and stepped through in GDB/pwndbg, checking `eflags` after each instruction. All programs start with `eflags = 0x202 [ IF ]`.

## Summary of the flags

| Program | Instruction | eflags | Set | Cleared | Why |
|---|---|---|---|---|---|
| add1 | `add al, [num2]` (120 + 10 = 130) | `0xA96` | PF AF SF IF OF | CF, ZF | 130 (`10000010`) fits in 8 bits unsigned so no carry, but it is above +127 so the signed result overflowed into a negative (OF, SF). Two 1-bits is even (PF), and `0x8 + 0xA` carries into the upper nibble (AF). |
| add2 | `add ax, [num2]` (32000 + 500 = 32500) | `0x202` | IF | CF, OF, SF, ZF, PF, AF | 32500 fits both unsigned and signed 16 bit ranges, the top bit is 0, the result is not zero, and the low byte `0xF4` (`11110100`) has five 1-bits, which is odd. |
| add3 | `add ax, [num2]` (0xFFFF + 1) | `0x257` | CF PF AF ZF IF | OF, SF | The sum needs 17 bits so the carry is set (CF) and the 16 bit result wraps to 0 (ZF, PF, and AF from `0xF + 1`). As a signed operation -1 + 1 = 0, so there is no overflow. |
| add3 | `adc ax, 0` (0 + 0 + CF) | `0x202` | IF | CF, ZF, PF, AF, SF, OF | The result is 1, so it is non-zero, positive, has an odd number of 1-bits and generates no carry. The flags from the `add` were overwritten. |

IF is set in every row because the operating system leaves the interrupt flag on for normal user processes, no arithmetic instruction changes it. When a program runs to completion, `xor ebx, ebx` overwrites the flags with `0x246 [ PF ZF IF ]` (the result is 0, so ZF is set, and zero 1-bits is even, so PF is set).

---

## ADDITION 1 PROGRAM

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

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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

---

## ADDITION 2 PROGRAM

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

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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

---

## ADDITION 3 PROGRAM

Utilising the source code below:
```asm
section .data
    num1 dw 0xFFFF ; 1111111111111111   65535
    num2 dw 1
    result dw 0

section .text
    global _start

_start:
    mov ax, [num1]
    add ax, [num2]       ; AX = 0xFFFF + 1 → 0 with CF=1
    adc ax, 0            ; AX = AX + CF → demonstrates ADC
    mov [result], ax

    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     add    ax,WORD PTR ds:0x804a002
   0x0804900d <+13>:    adc    ax,0x0
   0x08049011 <+17>:    mov    ds:0x804a004,ax
   0x08049017 <+23>:    mov    eax,0x1
   0x0804901c <+28>:    xor    ebx,ebx
   0x0804901e <+30>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <num1>:       -1
pwndbg> x/hu 0x804a000
0x804a000 <num1>:       65535
pwndbg> x/hd 0x804a002
0x804a002 <num2>:       1
pwndbg> x/hd 0x804a004
0x804a004 <result>:     0
pwndbg> 
```

> `x/hd` reads `0xFFFF` as a signed halfword, so it prints `-1`. We can use `x/hu` to see the unsigned value `65535`.

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./add/add3.asm, line 13.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/add/add3 

Breakpoint 1, _start () at ./add/add3.asm:13
...
   13 _start:
 ► 14     mov ax, [num1]
   15     add ax, [num2]       ; AX = 0xFFFF + 1 → 0 with CF=1
   16     adc ax, 0            ; AX = AX + CF → demonstrates ADC
   17     mov [result], ax
   18 
   19     mov eax, 1
   20     xor ebx, ebx
   21     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `add` (2 instructions) and investigate the flags
```bash
pwndbg> ni 2
...
 ► 0x804900d <_start+13>    adc    ax, 0
...
pwndbg> p/x $ax
$1 = 0x0
pwndbg> info reg eflags
eflags         0x257               [ CF PF AF ZF IF ]
pwndbg>
```

`0xFFFF + 1` needs 17 bits (`1 0000 0000 0000 0000`), but `AX` only holds 16, so the result wraps to `0x0000` and the extra bit is left in the carry flag:
- CF (Carry Flag) - the unsigned result overflowed 16 bits (65535 + 1 = 65536 > 65535), the carry out of the most significant bit is 1
- PF (Parity Flag) - the lower 8 bits are `00000000`, 0 number of 1s which is even
- AF (Auxilliary Flag) - there is a carry from the lower nibble to the upper nibble (`0xF + 1`)
- ZF (Zero Flag) - the result is `0`
- IF (Interrupt Flag) - controls whether the CPU responds to maskable hardware interrupts, set to 1 for normal user processes

The following flags are **not** set:
- SF (Sign Flag) - the most significant bit of the result is 0
- OF (Overflow Flag) - as a signed operation this is `-1 + 1 = 0`, which is within `-32768` to `32767`. So CF flags the unsigned overflow while OF stays clear for the signed one.

- Step over `adc` (1 instruction)
```bash
pwndbg> ni
...
 ► 0x8049011 <_start+17>    mov    word ptr [result], ax
...
pwndbg> p/d $ax
$2 = 1
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

`adc ax, 0` means `AX = AX + 0 + CF`, so `0 + 0 + 1 = 1`. The carry from the previous `add` is folded back into the result. This is how multi-word arithmetic is chained, the low word `add` produces the carry and the high word `adc` consumes it.

`adc` sets the flags again from its own result `0x0001`, so the previous flags are overwritten:
- CF is cleared, `0 + 0 + 1` does not carry out of bit 15
- ZF is cleared, the result is not `0`
- PF is cleared, `00000001` has 1 number of 1s which is odd
- AF is cleared, no carry from the lower nibble
- `IF` (Interrupt Flag) is the only flag set

```bash
pwndbg> ni
pwndbg> x/hd &result
0x804a004 <result>:     1
```

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```
