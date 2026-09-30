# MULTIPLICATION 3 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
