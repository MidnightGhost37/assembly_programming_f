# Logic and conditions

All five programs were assembled, linked, executed, and inspected with pwndbg in Kali WSL2 (`kali-linux`) on 16 October 2026. They use 32-bit Linux assembly. Every program exited with status `0` and produced **no terminal output**: the logical operations affect registers and flags, and none of these programs calls `write`.

## Build and run

Run these Bash commands from the repository root inside Kali WSL:

```bash
for src in 04_logic_and_conditions/*.asm; do
    name=$(basename "$src" .asm)
    nasm -f elf32 -g -F dwarf "$src" -o "04_logic_and_conditions/$name.o"
    ld -m elf_i386 "04_logic_and_conditions/$name.o" -o "04_logic_and_conditions/$name"
done

for name in and not or test xor; do
    echo "Running $name"
    "./04_logic_and_conditions/$name"
    echo "Exit status: $?"
done
```

The `Running` and `Exit status` messages come from the shell, not the programs. Executables and object files are beside the `.asm` sources in `04_logic_and_conditions/`. Object files are ignored by Git. The debug options allow pwndbg to show source lines.

## Instructions and observed results

`mov` loads the input bytes without changing flags. The usual inputs are `AL = 0xAA` (`10101010`) and `BL = 0xCC` (`11001100`). `test.asm` instead loads `BL = 0x0F` (`00001111`); `not.asm` only needs `AL`.

These values were read immediately after the logical instruction, before the exit sequence:

| Program | Instruction | Operation | Observed AL | Observed EFLAGS |
|---|---|---|---|---|
| `and.asm` | `and al, bl` | Keep bits set in both inputs: `10101010 & 11001100 = 10001000` | `0x88` (136) | `0x286 [ PF SF IF ]` |
| `not.asm` | `not al` | Invert every bit: `10101010` becomes `01010101` | `0x55` (85) | `0x202 [ IF ]`, unchanged |
| `or.asm` | `or al, bl` | Set bits present in either input: result `11101110` | `0xEE` (238) | `0x286 [ PF SF IF ]` |
| `test.asm` | `test al, bl` | Compute `10101010 & 00001111 = 00001010` only to set flags | `0xAA` (170), unchanged | `0x206 [ PF IF ]` |
| `xor.asm` | `xor al, bl` | Set bits that differ: result `01100110` | `0x66` (102) | `0x206 [ PF IF ]` |

For `and`, `or`, `xor`, and `test`:

- `ZF` is set for a zero result. It is clear in all four examples.
- `SF` copies bit 7 of the byte result. It is set for `0x88` and `0xEE`.
- `PF` is set for even parity in the result byte. `0x88`, `0xEE`, `0x0A`, and `0x66` contain two, six, two, and four set bits respectively, so all have `PF = 1`.
- `CF` and `OF` are cleared. `AF` is undefined; its displayed value is not a meaningful result.

`not` changes no flags. Its observed `0x202` was the initial flags value, not a value computed from `0x55`. `IF` was already set and is unaffected by these operations.

## Inspect with pwndbg

```bash
pwndbg -q 04_logic_and_conditions/and
```

In this installation the standalone launcher is `/home/kaude37/.local/bin/pwndbg`; use that full path if it is missing from `PATH`.

```text
pwndbg> starti
pwndbg> disassemble _start
pwndbg> x/1bx &val1
pwndbg> x/1bx &val2
pwndbg> si
pwndbg> si
pwndbg> si
pwndbg> info registers eax ebx eflags
eax            0x88
ebx            0xcc
eflags         0x286  [ PF SF IF ]
```

The register lines are shortened from the observed session. `starti` stops before the first instruction, and the three `si` commands execute the two loads and the logical operation. Repeat with `or`, `test`, or `xor`. For `not`, use two `si` commands (one load and one operation), and omit the `val2` inspection because that symbol does not exist. Use `p/x $al` to inspect just the result byte.

`test` leaves both operands unchanged, so its computed result is reflected only in flags. For example, `AL` stays `0xAA` while `ZF = 0` shows that `AL & BL` was nonzero.

## Exit instructions

Every program ends with:

```asm
mov eax, 1       ; 32-bit Linux sys_exit
xor ebx, ebx     ; exit status 0
int 0x80
```

There is no 32-bit `sys_write` call (`EAX = 4`). Inspect the logical result before the exit sequence: `mov eax, 1` replaces `AL`, and `xor ebx, ebx` overwrites the flags with the flags for zero (`0x246 [ PF ZF IF ]` in this environment).
