# MULTIPLICATION PROGRAMS

Three programs using the unsigned `mul`. `MUL` only defines two flags: **CF and OF are set together when the upper half of the product (`AH`, `DX` or `EDX`) is not zero**, and cleared when it is zero. SF, ZF, AF and PF are **undefined** after `MUL` (per the Intel manual), so we do not rely on them.

Each program was assembled with `nasm -f elf32`, linked with `ld -m elf_i386` (see [the build notes](../readme.md)) and stepped through in GDB/pwndbg, checking `eflags` after each instruction. All programs start with `eflags = 0x202 [ IF ]`.

## Summary of the flags

| Program | Instruction | eflags | Set | Cleared | Why |
|---|---|---|---|---|---|
| mul1 | `mul byte [num2]` (25 * 10 = 250) | `0x202` | IF | CF, OF | 250 fits in `AL`, so `AH` is 0 and the product did not spill into the upper half. |
| mul2 | `mul word [num2]` (3000 * 200 = 600000) | `0xA03` | CF IF OF | - | 600000 is larger than 65535, so `DX` = 9 is not zero and the product spilled into the upper half. |
| mul3 | `mul dword [num2]` (100000 * 300000 = 3*10^10) | `0xA03` | CF IF OF | - | The product needs 35 bits, so `EDX` = 6 is not zero and the product spilled into the upper half. |

IF is set in every row because the operating system leaves the interrupt flag on for normal user processes, no arithmetic instruction changes it. When a program runs to completion, `xor ebx, ebx` overwrites the flags with `0x246 [ PF ZF IF ]` (the result is 0, so ZF is set, and zero 1-bits is even, so PF is set).

---

## MULTIPLICATION 1 PROGRAM

Utilising the source code below:
```asm
; mul_byte.asm
section .data
    num1 db 25
    num2 db 10
    result dw 0         ; needs 16 bits for result

section .text
    global _start

_start:
    mov al, [num1]      ; al = first operand
    mul byte [num2]     ; ax = al * num2 (25 * 10 = 250)
    mov [result], ax    ; store result in memory

    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    al,ds:0x804a000
   0x08049005 <+5>:     mul    BYTE PTR ds:0x804a001
   0x0804900b <+11>:    mov    ds:0x804a002,ax
   0x08049011 <+17>:    mov    eax,0x1
   0x08049016 <+22>:    xor    ebx,ebx
   0x08049018 <+24>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/bd 0x804a000
0x804a000 <num1>:       25
pwndbg> x/bd 0x804a001
0x804a001 <num2>:       10
pwndbg> x/hd 0x804a002
0x804a002 <result>:     0
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./mul/mul1.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/mul/mul1 

Breakpoint 1, _start () at ./mul/mul1.asm:11
...
   10 _start:
 ► 11     mov al, [num1]      ; al = first operand
   12     mul byte [num2]     ; ax = al * num2 (25 * 10 = 250)
   13     mov [result], ax    ; store result in memory
   14 
   15     mov eax, 1
   16     xor ebx, ebx
   17     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `mul` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900b <_start+11>    mov    word ptr [result], ax
...
pwndbg> p/x $ax
$1 = 0xfa
pwndbg> p/d $ax
$2 = 250
pwndbg> p/d $ah
$3 = 0
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

`mul byte [num2]` is an 8 bit multiplication, the operands are always `AL` and the memory byte, and the product is written to the whole of `AX`:
- `AX` = `25 * 10` = `250` (`0xFA`)
- `AH` = `0`, the product fits in the lower byte `AL`

`MUL` defines only two flags, CF (Carry Flag) and OF (Overflow Flag). They are both set when the upper half of the product (here `AH`) is not zero, and cleared when it is zero. `AH` is `0`, so CF = 0 and OF = 0. SF, ZF, AF and PF are **undefined** after a `MUL` (per the Intel manual), so we do not rely on them. `IF` (Interrupt Flag) is the only flag we expect to see, set to 1 for normal user processes.

> If the product was bigger than 255, for example `25 * 11 = 275`, `AH` would be `1` and both CF and OF would be set. It is how we know that the result no longer fits in the 8 bit register.

- Store the result in memory
```bash
pwndbg> ni
pwndbg> x/hd &result
0x804a002 <result>:     250
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

## MULTIPLICATION 2 PROGRAM

Utilising the source code below:
```asm
section .data
    num1 dw 3000   ; 1011 10111000
    num2 dw 200    ;      11001000
    result dd 0    ; 32-bit result 1001 00100111 11000000

section .text
    global _start

_start:
    mov ax, [num1]      ; moving the value from num1 to ax
    mul word [num2]     ; DX:AX = AX * num2
    mov [result], ax    ; lower 16 bits
    mov [result+2], dx  ; upper 16 bits

    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     mul    WORD PTR ds:0x804a002
   0x0804900d <+13>:    mov    ds:0x804a004,ax
   0x08049013 <+19>:    mov    WORD PTR ds:0x804a006,dx
   0x0804901a <+26>:    mov    eax,0x1
   0x0804901f <+31>:    xor    ebx,ebx
   0x08049021 <+33>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <num1>:       3000
pwndbg> x/hd 0x804a002
0x804a002 <num2>:       200
pwndbg> x/wd 0x804a004
0x804a004 <result>:     0
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./mul/mul2.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/mul/mul2 

Breakpoint 1, _start () at ./mul/mul2.asm:11
...
   10 _start:
 ► 11     mov ax, [num1]      ; moving the value from num1 to ax
   12     mul word [num2]     ; DX:AX = AX * num2
   13     mov [result], ax    ; lower 16 bits
   14     mov [result+2], dx  ; upper 16 bits
   15 
   16     mov eax, 1
   17     xor ebx, ebx
   18     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `mul` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900d <_start+13>    mov    word ptr [result], ax
...
pwndbg> p/x $ax
$1 = 0x27c0
pwndbg> p/d $ax
$2 = 10176
pwndbg> p/d $dx
$3 = 9
pwndbg> info reg eflags
eflags         0xa03               [ CF IF OF ]
pwndbg>
```

`mul word [num2]` is a 16 bit multiplication, the operands are `AX` and the memory word, and the 32 bit product is written to the pair `DX:AX` (`DX` is the high word, `AX` the low word):
- `3000 * 200` = `600000` = `0x927C0`
- `DX` = `0x0009` (`9`) and `AX` = `0x27C0` (`10176`), so `DX:AX` = `0x000927C0`

The product is larger than 65535 so it does not fit in `AX` alone, and the extra bits spill into `DX`. That is what the flags report:
- CF (Carry Flag) - the upper half of the product (`DX`) is not zero
- OF (Overflow Flag) - the upper half of the product (`DX`) is not zero, they are always set and cleared together after a `MUL`
- IF (Interrupt Flag) - set to 1 for normal user processes

SF, ZF, AF and PF are **undefined** after a `MUL` (per the Intel manual), so we do not rely on them, and a real run may show some of them set.

- Store the result in memory (2 instructions)
```bash
pwndbg> ni 2
pwndbg> x/wd &result
0x804a004 <result>:     600000
pwndbg> x/2hx &result
0x804a004 <result>:     0x27c0  0x0009
```

The low word is stored first (`result`) then the high word (`result+2`), which matches the little-endian layout of the 32 bit value `0x000927C0`.

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```

---

## MULTIPLICATION 3 PROGRAM

Utilising the source code below:
```asm
section .data
    num1 dd 100000
    num2 dd 300000
    result dq 0 ; 64-bit result 30 000 000 000
    ; 110 11111100 00100011 10101100 00000000
section .text
    global _start

_start:
    mov eax, [num1]
    mul dword [num2]    ; edx:eax = eax * num2
    mov [result], eax   ; 4 bytes low 32 bits
    mov [result+4], edx ; 4 bytes high 32 bits

    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    eax,ds:0x804a000
   0x08049005 <+5>:     mul    DWORD PTR ds:0x804a004
   0x0804900b <+11>:    mov    ds:0x804a008,eax
   0x08049010 <+16>:    mov    DWORD PTR ds:0x804a00c,edx
   0x08049016 <+22>:    mov    eax,0x1
   0x0804901b <+27>:    xor    ebx,ebx
   0x0804901d <+29>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/wd 0x804a000
0x804a000 <num1>:       100000
pwndbg> x/wd 0x804a004
0x804a004 <num2>:       300000
pwndbg> x/gd 0x804a008
0x804a008 <result>:     0
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./mul/mul3.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/mul/mul3 

Breakpoint 1, _start () at ./mul/mul3.asm:11
...
   10 _start:
 ► 11     mov eax, [num1]
   12     mul dword [num2]    ; edx:eax = eax * num2
   13     mov [result], eax   ; 4 bytes low 32 bits
   14     mov [result+4], edx ; 4 bytes high 32 bits
   15 
   16     mov eax, 1
   17     xor ebx, ebx
   18     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov` and `mul` (2 instructions) and investigate the registers and flags
```bash
pwndbg> ni 2
...
 ► 0x804900b <_start+11>    mov    dword ptr [result], eax
...
pwndbg> p/x $eax
$1 = 0xfc23ac00
pwndbg> p/u $eax
$2 = 4230196224
pwndbg> p/d $edx
$3 = 6
pwndbg> info reg eflags
eflags         0xa03               [ CF IF OF ]
pwndbg>
```

`mul dword [num2]` is a 32 bit multiplication, the operands are `EAX` and the memory dword, and the 64 bit product is written to the pair `EDX:EAX`:
- `100000 * 300000` = `30000000000` = `0x6FC23AC00`
- `EDX` = `0x00000006` (`6`) and `EAX` = `0xFC23AC00` (`4230196224`), so `EDX:EAX` = `0x00000006FC23AC00`

`p/d $eax` would print `-64771072`, because `0xFC23AC00` has its top bit set and is read as a signed number. We use `p/u` to see the unsigned value, which is what `MUL` works with.

The product needs 35 bits (`110` followed by the 32 bits `11111100 00100011 10101100 00000000`, as in the source comment), so it cannot fit in `EAX` alone. `EDX` is not zero, hence:
- CF (Carry Flag) - set, the upper half of the product (`EDX`) is not zero
- OF (Overflow Flag) - set, for the same reason
- IF (Interrupt Flag) - set to 1 for normal user processes

SF, ZF, AF and PF are **undefined** after a `MUL` (per the Intel manual), so we do not rely on them, and a real run may show some of them set.

- Store the result in memory (2 instructions)
```bash
pwndbg> ni 2
pwndbg> x/gd &result
0x804a008 <result>:     30000000000
pwndbg> x/2wx &result
0x804a008 <result>:     0xfc23ac00      0x00000006
```

The low dword is stored first (`result`) then the high dword (`result+4`), which matches the little-endian layout of the 64 bit value.

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```
