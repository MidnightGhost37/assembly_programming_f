# SUBTRACTION 3 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
