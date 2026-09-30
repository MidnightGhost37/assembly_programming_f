# SUBTRACTION 2 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
