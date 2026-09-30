# DIVISION PROGRAMS

Three programs using the unsigned `div`. **All the arithmetic flags (CF, OF, SF, ZF, AF, PF) are undefined after `DIV`** (per the Intel manual), so a zero remainder, for example, does not set ZF, and we do not rely on them. What `DIV` does define is the result registers (`AL`/`AH`, `AX`/`DX`, `EAX`/`EDX`) and the fault behaviour: a divisor of 0, or a quotient too large for the destination register, raises a divide error (`SIGFPE`).

Each program was assembled with `nasm -f elf32`, linked with `ld -m elf_i386` (see [the build notes](../readme.md)) and stepped through in GDB/pwndbg, checking `eflags` after each instruction. All programs start with `eflags = 0x202 [ IF ]`.

## Summary of the flags

| Program | Instruction | eflags | Set | Cleared | Why |
|---|---|---|---|---|---|
| div1 | `div bl` (100 / 7) | `0x202` | IF | none defined | `AL` = 14 (quotient), `AH` = 2 (remainder). |
| div2 | `div bx` (50000 / 300) | `0x202` | IF | none defined | `AX` = 166 (quotient), `DX` = 200 (remainder). |
| div3 | `div ebx` (300000000 / 1000) | `0x202` | IF | none defined | `EAX` = 300000 (quotient), `EDX` = 0 (remainder). |

IF is set in every row because the operating system leaves the interrupt flag on for normal user processes, no arithmetic instruction changes it. When a program runs to completion, `xor ebx, ebx` overwrites the flags with `0x246 [ PF ZF IF ]` (the result is 0, so ZF is set, and zero 1-bits is even, so PF is set).

---

## DIVISION 1 PROGRAM

Utilising the source code below:
```asm
; al = quotient, ah = remainder

section .data
    dividend dw 100   ; ax = 100
    divisor  db 7     ; bl = 7

section .text
    global _start

_start:
    mov ax, [dividend]  ; ax = 100
    mov bl, [divisor]   ; bl = 7
    div bl              ; al = 14, ah = 2

    ; Exit
    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     mov    bl,BYTE PTR ds:0x804a002
   0x0804900c <+12>:    div    bl
   0x0804900e <+14>:    mov    eax,0x1
   0x08049013 <+19>:    xor    ebx,ebx
   0x08049015 <+21>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hd 0x804a000
0x804a000 <dividend>:   100
pwndbg> x/bd 0x804a002
0x804a002 <divisor>:    7
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./div/div1.asm, line 11.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/div/div1 

Breakpoint 1, _start () at ./div/div1.asm:11
...
   10 _start:
 ► 11     mov ax, [dividend]  ; ax = 100
   12     mov bl, [divisor]   ; bl = 7
   13     div bl              ; al = 14, ah = 2
   14 
   15     ; Exit
   16     mov eax, 1
   17     xor ebx, ebx
   18     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over `mov`, `mov` and `div` (3 instructions)
```bash
pwndbg> ni 3
...
 ► 0x804900e <_start+14>    mov    eax, 1
...
```

- Investigate registers and flags
```bash
pwndbg> p $ax
$1 = 526
pwndbg> p/x $ax
$2 = 0x20e
pwndbg> p/d $al
$3 = 14
pwndbg> p/d $ah
$4 = 2
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

`div bl` is an 8 bit division, the dividend is always `AX` and the divisor is `BL`:
- `AL` = quotient = `100 / 7` = `14`
- `AH` = remainder = `100 % 7` = `2` (`14 * 7 = 98`, `100 - 98 = 2`)

Both results are written back into `AX`, `AH` (upper byte) `0x02` and `AL` (lower byte) `0x0E`, hence `AX = 0x020E` (`526`). Reading `AX` as one number is not the quotient, so we use `$al` and `$ah` to read the results.

`DIV` leaves its flags **undefined** (per the Intel manual), CF, OF, SF, ZF, AF and PF are not meaningful after a division. Hence we do not rely on them, `IF` (Interrupt Flag) is the only flag we expect to see, set to 1 for normal user processes.

> The quotient must fit in `AL` (0 to 255). If it does not, for example `AX = 1000` and `BL = 2` (quotient 500), the CPU raises a divide error and the program is killed with `SIGFPE`. Dividing by `0` does the same.

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```

---

## DIVISION 2 PROGRAM

Utilising the source code below:
```asm
; ax = quotient, dx = remainder

section .data
    dividend dw 50000   ; Low word
    highpart dw 0       ; High word (DX=0)
    divisor  dw 300

section .text
    global _start

_start:
    mov ax, [dividend]  ; AX = 50000
    mov dx, [highpart]  ; DX = 0
    mov bx, [divisor]   ; BX = 300
    div bx              ; AX = quotient, 166 
                        ; DX = remainder, 200

    ; Exit call
    mov eax, 1     ;sys call number to exit
    xor ebx, ebx   ; 0 for successful exit
    int 0x80       ; invoke call
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    ax,ds:0x804a000
   0x08049006 <+6>:     mov    dx,WORD PTR ds:0x804a002
   0x0804900d <+13>:    mov    bx,WORD PTR ds:0x804a004
   0x08049014 <+20>:    div    bx
   0x08049017 <+23>:    mov    eax,0x1
   0x0804901c <+28>:    xor    ebx,ebx
   0x0804901e <+30>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/hu 0x804a000
0x804a000 <dividend>:   50000
pwndbg> x/hd 0x804a002
0x804a002 <highpart>:   0
pwndbg> x/hd 0x804a004
0x804a004 <divisor>:    300
pwndbg> 
```

> `x/hd` reads `50000` (`0xC350`) as a signed halfword and prints `-15536`. We use `x/hu` to see the unsigned value.

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./div/div2.asm, line 12.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/div/div2 

Breakpoint 1, _start () at ./div/div2.asm:12
...
   11 _start:
 ► 12     mov ax, [dividend]  ; AX = 50000
   13     mov dx, [highpart]  ; DX = 0
   14     mov bx, [divisor]   ; BX = 300
   15     div bx              ; AX = quotient, 166 
   16                         ; DX = remainder, 200
   17 
   18     ; Exit call
   19     mov eax, 1     ;sys call number to exit
   20     xor ebx, ebx   ; 0 for successful exit
   21     int 0x80       ; invoke call

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over the three `mov` and the `div` (4 instructions)
```bash
pwndbg> ni 4
...
 ► 0x8049017 <_start+23>    mov    eax, 1
...
```

- Investigate registers and flags
```bash
pwndbg> p/d $ax
$1 = 166
pwndbg> p/x $ax
$2 = 0xa6
pwndbg> p/d $dx
$3 = 200
pwndbg> p/x $dx
$4 = 0xc8
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

`div bx` is a 16 bit division, the dividend is the 32 bit pair `DX:AX` (`DX` is the high word, `AX` the low word) and the divisor is `BX`:
- `AX` = quotient = `50000 / 300` = `166`
- `DX` = remainder = `50000 % 300` = `200` (`166 * 300 = 49800`, `50000 - 49800 = 200`)

That is why `highpart` is loaded into `DX` before dividing, `DX` is part of the dividend. If an old value was left in it, we would be dividing a much larger number.

`DIV` leaves its flags **undefined** (per the Intel manual), they are not meaningful after a division. `IF` (Interrupt Flag) is the only flag we expect to see.

> The quotient must fit in `AX` (0 to 65535), which requires `DX < BX`. Here `0 < 300`. If `DX >= BX` the quotient would not fit and the CPU raises a divide error (`SIGFPE`), as it does when dividing by `0`.

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```

---

## DIVISION 3 PROGRAM

Utilising the source code below:
```asm
; Unsigned division: EDX:EAX / r/m32 → EAX = quotient, EDX = remainder

section .data
    dividend dd 300000000   ; Low part
    highpart dd 0           ; High part
    divisor  dd 1000

section .text
    global _start

_start:
    mov eax, [dividend]
    mov edx, [highpart]
    mov ebx, [divisor]
    div ebx                 ; EAX = 300000, EDX = 0

    ; Exit
    mov eax, 1
    xor ebx, ebx
    int 0x80
```

Debuging and analyzing:
```bash
pwndbg> disass _start
Dump of assembler code for function _start:
   0x08049000 <+0>:     mov    eax,ds:0x804a000
   0x08049005 <+5>:     mov    edx,DWORD PTR ds:0x804a004
   0x0804900b <+11>:    mov    ebx,DWORD PTR ds:0x804a008
   0x08049011 <+17>:    div    ebx
   0x08049013 <+19>:    mov    eax,0x1
   0x08049018 <+24>:    xor    ebx,ebx
   0x0804901a <+26>:    int    0x80
End of assembler dump.
pwndbg> 

# CONFIRM THE NUMBERS
pwndbg> x/wd 0x804a000
0x804a000 <dividend>:   300000000
pwndbg> x/wd 0x804a004
0x804a004 <highpart>:   0
pwndbg> x/wd 0x804a008
0x804a008 <divisor>:    1000
pwndbg> 
```

### STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

We can run and debug the program:
- Set Breakpoints
```bash
pwndbg> b _start
Breakpoint 1 at 0x8049000: file ./div/div3.asm, line 12.
pwndbg> 
```

- Run program:
```bash
pwndbg> r
Starting program: /mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic/div/div3 

Breakpoint 1, _start () at ./div/div3.asm:12
...
   11 _start:
 ► 12     mov eax, [dividend]
   13     mov edx, [highpart]
   14     mov ebx, [divisor]
   15     div ebx                 ; EAX = 300000, EDX = 0
   16 
   17     ; Exit
   18     mov eax, 1
   19     xor ebx, ebx
   20     int 0x80

...
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

- Step over the three `mov` and the `div` (4 instructions)
```bash
pwndbg> ni 4
...
 ► 0x8049013 <_start+19>    mov    eax, 1
...
```

- Investigate registers and flags
```bash
pwndbg> p/d $eax
$1 = 300000
pwndbg> p/x $eax
$2 = 0x493e0
pwndbg> p/d $edx
$3 = 0
pwndbg> info reg eflags
eflags         0x202               [ IF ]
pwndbg>
```

`div ebx` is a 32 bit division, the dividend is the 64 bit pair `EDX:EAX` and the divisor is `EBX`:
- `EAX` = quotient = `300000000 / 1000` = `300000` (`0x493E0`)
- `EDX` = remainder = `300000000 % 1000` = `0`, it divides exactly

The `dividend` is `300000000` = `0x11E1A300`, which is stored little-endian in memory as `00 a3 e1 11`. `EDX` is `0` so the whole dividend is just `EAX`.

`DIV` leaves its flags **undefined** (per the Intel manual), they are not meaningful after a division, so a remainder of `0` does **not** set ZF. `IF` (Interrupt Flag) is the only flag we expect to see.

> The quotient must fit in `EAX` (0 to 4294967295), which requires `EDX < EBX`. Otherwise, or if the divisor is `0`, the CPU raises a divide error (`SIGFPE`).

> If the program is allowed to complete the `xor ebx, ebx` command resets the flags leaving PF, ZF, IF. PF (parity flag) since 0 number of 1s which is considered even, ZF (Zero Flag) since the result is 0 and IF is set to 1 for normal user processes.

```bash
pwndbg> ni 2
...

pwndbg> info reg eflags
eflags         0x246               [ PF ZF IF ]
pwndbg> 
```
