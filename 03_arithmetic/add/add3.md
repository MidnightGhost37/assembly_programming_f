# ADDITION 3 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
