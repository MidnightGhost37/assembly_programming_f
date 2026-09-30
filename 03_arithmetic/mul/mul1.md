# MULTIPLICATION 1 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
