# SUBTRACTION PROGRAMS

Three programs using `sub` and `sbb`. On a subtraction CF is the **borrow** (set when the first number is smaller than the second as unsigned numbers), OF is the **signed** overflow (the operands have different signs and the result has the sign of the subtrahend), SF copies the top bit of the result, ZF is set when the result is 0, PF looks at the lowest byte only, and AF is a borrow between bit 4 and bit 3.

Each program was assembled with `nasm -f elf32`, linked with `ld -m elf_i386` (see [the build notes](../readme.md)) and stepped through in GDB/pwndbg, checking `eflags` after each instruction. All programs start with `eflags = 0x202 [ IF ]`.

## Summary of the flags

| Program | Instruction | eflags | Set | Cleared | Why |
|---|---|---|---|---|---|
| sub1 | `sub al, [num2]` (50 - 80) | `0x287` | CF PF SF IF | ZF, AF, OF | 50 < 80 so a borrow was needed (CF). The result `0xE2` (`11100010`, -30) has its top bit set (SF) and four 1-bits (PF). -30 is inside -128..127 so there is no signed overflow. |
| sub2 | `sub ax, [num2]` (1000 - 2000) | `0x287` | CF PF SF IF | ZF, AF, OF | 1000 < 2000 so a borrow was needed (CF). The result `0xFC18` (-1000) has its top bit set (SF) and the low byte `0x18` has two 1-bits (PF). -1000 fits in 16 bits so OF is clear. |
| sub3 | `sub ax, [num2]` (0 - 1) | `0x297` | CF PF AF SF IF | ZF, OF | A borrow is needed from beyond the top bit (CF) and from the upper nibble (AF). The result `0xFFFF` has its top bit set (SF) and eight 1-bits (PF). -1 fits so OF is clear. |
| sub3 | `sbb ax, 0` (AX - 0 - CF) | `0x282` | SF IF | CF, ZF, PF, AF, OF | `0xFFFF - 1 = 0xFFFE` needs no borrow (CF, AF cleared), still has the top bit set (SF), and the low byte `11111110` has seven 1-bits, which is odd (PF cleared). |

IF is set in every row because the operating system leaves the interrupt flag on for normal user processes, no arithmetic instruction changes it. When a program runs to completion, `xor ebx, ebx` overwrites the flags with `0x246 [ PF ZF IF ]` (the result is 0, so ZF is set, and zero 1-bits is even, so PF is set).

---

## SUBTRACTION 1 PROGRAM

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

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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

---

## SUBTRACTION 2 PROGRAM

Utilising the source code below:
```asm
; sub16.asm
section .data
    num1 dw 1000
    num2 dw 2000
    result dw 0

section .text
    global _start

_start:
    mov ax, [num1]
    sub ax, [num2]       ; AX = 1000 - 2000
    mov [result], ax


exit:
    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     sub    ax,WORD PTR ds:0x804a002
   0x0804900d <+13>:    mov    ds:0x804a004,ax
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <num1>:       1000
pwndbg> x/hd 0x804a002
0x804a002 <num2>:       2000
pwndbg> x/hd 0x804a004
0x804a004 <result>:     0
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b *_start
Breakpoint 1 at 0x8049000: file ./sub/sub2.asm, line 11.
pwndbg> b *exit
Breakpoint 2 at 0x8049013: file ./sub/sub2.asm, line 17.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/sub/sub2 

Breakpoint 1, _start () at ./sub/sub2.asm:11
...
   10 _start:
 ► 11     mov ax, [num1]
   12     sub ax, [num2]       ; AX = 1000 - 2000
   13     mov [result], ax
   14 
   15 
   16 exit:
   17     mov eax, 1
   18     xor ebx, ebx
   19     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `sub` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900d <_start+13>    mov    word ptr [result], ax
...
pwndbg> p/x $ax
$1 = 0xfc18
pwndbg> p/t $ax
$2 = 1111110000011000
pwndbg> p/d $ax
$3 = -1000
pwndbg> p/u $ax
$4 = 64536
pwndbg> info reg eflags
eflags         0x287               [ CF PF SF IF ]
pwndbg>
```

The subtraction `1000 - 2000` gives `-1000`, which as a 16 bit two's complement number is `0xFC18` (`65536 - 1000 = 64536` if read as unsigned).

From the program, the following flags are set:
- CF (Carry Flag) - the borrow flag, `1000` is smaller than `2000` as unsigned numbers
- PF (Parity Flag) - the lower 8 bits of the result are `0x18` (`00011000`), 2 number of 1s which is even. PF only looks at the lower byte, even in a 16 bit operation
- SF (Sign Bit Flag) - the most significant bit is set (1), the result is negative
- IF (Interrupt Flag) - controls whether the CPU responds to maskable hardware interrupts, set to 1 for normal user processes

The following flags are **not** set:
- ZF (Zero Flag) - the result is not `0`
- AF (Auxilliary Flag) - no borrow from the upper nibble to the lower nibble (`0x8 - 0x0` needs no borrow)
- OF (Overflow Flag) - as a signed operation `-1000` is within `-32768` to `32767`

- Store the result and continue to the exit label
```bash
pwndbg> c
Continuing.

Breakpoint 2, exit () at ./sub/sub2.asm:17
...
pwndbg> x/hd &result
0x804a004 <result>:     -1000
pwndbg> info reg eflags
eflags         0x287               [ CF PF SF IF ]
pwndbg> 
```

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```

---

## SUBTRACTION 3 PROGRAM

Utilising the source code below:
```asm
; sbb.asm
section .data
    num1 dw 0x0000
    num2 dw 1
    result dw 0

section .text
    global _start

_start:
    mov ax, [num1]
    sub ax, [num2]       ; AX = 0 - 1 → FFFFh, CF=1
    sbb ax, 0            ; AX = AX - CF
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
   0x08049006 <+6>:     sub    ax,WORD PTR ds:0x804a002
   0x0804900d <+13>:    sbb    ax,0x0
   0x08049011 <+17>:    mov    ds:0x804a004,ax
   0x08049017 <+23>:    mov    eax,0x1
   0x0804901c <+28>:    xor    ebx,ebx
   0x0804901e <+30>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <num1>:       0
pwndbg> x/hd 0x804a002
0x804a002 <num2>:       1
pwndbg> x/hd 0x804a004
0x804a004 <result>:     0
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./sub/sub3.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/sub/sub3 

Breakpoint 1, _start () at ./sub/sub3.asm:11
...
   10 _start:
 ► 11     mov ax, [num1]
   12     sub ax, [num2]       ; AX = 0 - 1 → FFFFh, CF=1
   13     sbb ax, 0            ; AX = AX - CF
   14     mov [result], ax
   15 
   16     mov eax, 1
   17     xor ebx, ebx
   18     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `sub` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900d <_start+13>    sbb    ax, 0
...
pwndbg> p/x $ax
$1 = 0xffff
pwndbg> info reg eflags
eflags         0x297               [ CF PF AF SF IF ]
pwndbg>
```

`0 - 1` cannot be done without a borrow, so the result wraps around to `0xFFFF` (`-1` signed, `65535` unsigned):
- CF (Carry Flag) - the borrow flag, `0` is smaller than `1` as unsigned numbers
- PF (Parity Flag) - the lower 8 bits are `11111111`, 8 number of 1s which is even
- AF (Auxilliary Flag) - there is a borrow from the upper nibble to the lower nibble
- SF (Sign Bit Flag) - the most significant bit is set (1)
- IF (Interrupt Flag) - controls whether the CPU responds to maskable hardware interrupts, set to 1 for normal user processes

The following flags are **not** set:
- ZF (Zero Flag) - the result is not `0`
- OF (Overflow Flag) - as a signed operation `0 - 1 = -1` is within `-32768` to `32767`

- Step over `sbb` (1 instruction)
```bash
pwndbg> ni
...
 ► 0x8049011 <_start+17>    mov    word ptr [result], ax
...
pwndbg> p/x $ax
$2 = 0xfffe
pwndbg> p/d $ax
$3 = -2
pwndbg> info reg eflags
eflags         0x282               [ SF IF ]
pwndbg>
```

`sbb ax, 0` means `AX = AX - 0 - CF`, so `0xFFFF - 0 - 1 = 0xFFFE` (`-2`). The borrow from the previous `sub` is taken out of the result. This is how multi-word subtraction is chained, the low word `sub` produces the borrow and the high word `sbb` consumes it.

`sbb` sets the flags again from its own result `0xFFFE`, so the previous flags are overwritten:
- CF is cleared, `0xFFFF - 1` does not need a borrow
- PF is cleared, the lower 8 bits are `11111110`, 7 number of 1s which is odd
- AF is cleared, `0xF - 0 - 1` does not need a borrow from the upper nibble
- SF stays set, the most significant bit of `0xFFFE` is 1
- `SF` and `IF` are the only flags set

- Store the result in memory
```bash
pwndbg> ni
pwndbg> x/hd &result
0x804a004 <result>:     -2
```

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```
