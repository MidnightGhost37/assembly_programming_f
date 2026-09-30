# This contains analysis of the assembly programs in contrast to EFLAGS (FLAGS SET)


## Preparations

The first thing to do was to ensure we compile the x32 programs that existed within the repository (we will compile the programs using the debug symbols for smooth debugging)

> Since the programs create object files, we will delete them as we are interested in the final output

```bash
$ pwd
/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic

$ bash build.sh
[+] Compilation succeeded for ./add/add1.asm!
[*] Linking files: ./add/add1.o -> ./add/add1
...
[*] Linking files: ./sub/sub2.o -> ./sub/sub2
[+] Compilation succeeded for ./sub/sub3.asm!
[*] Linking files: ./sub/sub3.o -> ./sub/sub3
...
```


## Analysis per operation

Every folder has a `README.md` with the full GDB walkthrough of its three programs and a summary table of which flags are set or cleared, and why.

| Folder | Programs | Instructions covered | Flags that are defined |
|---|---|---|---|
| [add](./add/README.md) | `add1`, `add2`, `add3` | `add`, `adc` | CF, PF, AF, ZF, SF, OF |
| [sub](./sub/README.md) | `sub1`, `sub2`, `sub3` | `sub`, `sbb` | CF (borrow), PF, AF, ZF, SF, OF |
| [mul](./mul/README.md) | `mul1`, `mul2`, `mul3` | `mul` (8, 16 and 32 bit) | CF and OF only |
| [div](./div/README.md) | `div1`, `div2`, `div3` | `div` (8, 16 and 32 bit) | none |

### Reading the flags

- **CF (Carry)** - unsigned overflow: the carry out of the top bit on an addition, or the borrow on a subtraction.
- **OF (Overflow)** - signed overflow: the result does not fit in the signed range (for example +127 for 8 bits).
- **SF (Sign)** - a copy of the most significant bit of the result.
- **ZF (Zero)** - the result is 0.
- **PF (Parity)** - the lowest byte of the result has an even number of 1-bits, even for 16 and 32 bit operations.
- **AF (Auxiliary)** - a carry or borrow between bit 3 and bit 4.
- **IF (Interrupt)** - not an arithmetic flag. The operating system leaves it on for user processes, which is why `eflags` starts as `0x202 [ IF ]` and IF is on in every dump.

`mul` defines only CF and OF (both set when the upper half of the product is not zero), and `div` leaves all of them undefined, so those two folders focus on the result registers instead. When any program is allowed to finish, `xor ebx, ebx` sets the flags to `0x246 [ PF ZF IF ]`.

### Results at a glance

| Program | Operation | Result | eflags |
|---|---|---|---|
| add1 | 120 + 10 (8 bit) | 130 (`0x82`) | `0xA96 [ PF AF SF IF OF ]` |
| add2 | 32000 + 500 (16 bit) | 32500 (`0x7EF4`) | `0x202 [ IF ]` |
| add3 | `0xFFFF + 1`, then `adc ax, 0` | `0`, then `1` | `0x257 [ CF PF AF ZF IF ]`, then `0x202 [ IF ]` |
| sub1 | 50 - 80 (8 bit) | -30 (`0xE2`) | `0x287 [ CF PF SF IF ]` |
| sub2 | 1000 - 2000 (16 bit) | -1000 (`0xFC18`) | `0x287 [ CF PF SF IF ]` |
| sub3 | `0 - 1`, then `sbb ax, 0` | `0xFFFF`, then `0xFFFE` | `0x297 [ CF PF AF SF IF ]`, then `0x282 [ SF IF ]` |
| mul1 | 25 * 10 (8 bit) | 250 in `AX` | `0x202 [ IF ]` |
| mul2 | 3000 * 200 (16 bit) | 600000 in `DX:AX` | `0xA03 [ CF IF OF ]` |
| mul3 | 100000 * 300000 (32 bit) | 30000000000 in `EDX:EAX` | `0xA03 [ CF IF OF ]` |
| div1 | 100 / 7 (8 bit) | `AL` = 14, `AH` = 2 | `0x202 [ IF ]` |
| div2 | 50000 / 300 (16 bit) | `AX` = 166, `DX` = 200 | `0x202 [ IF ]` |
| div3 | 300000000 / 1000 (32 bit) | `EAX` = 300000, `EDX` = 0 | `0x202 [ IF ]` |

