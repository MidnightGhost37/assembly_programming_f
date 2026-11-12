# 07 - The stack

## Guides

| Source | Guide | Focus |
|---|---|---|
| [01.asm](01.asm) | [01 guide](01_README.md) | Two pushes and pops into different registers |
| [02.asm](02.asm) | [02 guide](02_README.md) | 64-bit function frame and local variables |
| [03.asm](03.asm) | [03 guide](03_README.md) | Return address stored by `call` and consumed by `ret` |
| [04.asm](04.asm) | [04 guide](04_README.md) | 32-bit function frame and local variables |
| [05.asm](05.asm) | [05 guide](05_README.md) | 8-byte stack slots and little-endian storage |
| [06.asm](06.asm) | [06 guide](06_README.md) | 4-byte stack slots and little-endian storage |

## Build and run together

Use Linux or WSL with NASM, `ld`, and GDB. From the repository root:

```bash
mkdir -p build/07_stack
for n in 01 02 03 05; do
    nasm -f elf64 -g -F dwarf "07_stack/$n.asm" -o "build/07_stack/$n.o"
    ld -m elf_x86_64 "build/07_stack/$n.o" -o "07_stack/$n"
done
for n in 04 06; do
    nasm -f elf32 -g -F dwarf "07_stack/$n.asm" -o "build/07_stack/$n.o"
    ld -m elf_i386 "build/07_stack/$n.o" -o "07_stack/$n"
done
for n in 01 02 03 04 05 06; do
    "07_stack/$n"
    printf '%s: exit status %s\n' "$n" "$?"
done
```

Expect six status-`0` lines and no program output. The final executables sit beside their `.asm` sources; intermediate object files stay in the ignored `build/` directory. Programs `04` and `06` use the 32-bit Linux `int 0x80` exit; the others use the 64-bit `syscall` exit.
