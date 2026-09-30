# DIVISION 1 PROGRAM

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

## STEP BY STEP WALKTHROUGH AND FLAG COMPARISON

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
