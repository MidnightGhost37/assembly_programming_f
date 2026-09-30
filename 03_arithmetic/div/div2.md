# DIVISION 2 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
