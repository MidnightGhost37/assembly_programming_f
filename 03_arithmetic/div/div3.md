# DIVISION 3 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
