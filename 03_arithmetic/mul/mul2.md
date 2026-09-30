# MULTIPLICATION 2 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
