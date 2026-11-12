# 06.asm - 32-bit stack slots and little-endian bytes

[Assembly source](06.asm) | [Actual Pwndbg transcript](docs/06/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program pushes `0x11223344` and `0x1234` as two 4-byte values, then pops them back into EBX and EAX. The register values and starting ESP are restored before exit setup overwrites EAX and EBX. It exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0xffffcd10**, the value of `ESP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **4 bytes** from `ESP` before storing its value; `pop` reads at the current top and then adds **4 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `ESP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | ESP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x08049000` | `mov    eax,0x11223344` | `0xffffcd10` -> `0xffffcd10` | 0 | Load the 32-bit pattern 0x11223344 into EAX. |
| `0x08049005` | `mov    ebx,0x1234` | `0xffffcd10` -> `0xffffcd10` | 0 | Load EBX=0x1234; the operand occupies a full 32-bit register. |
| `0x0804900a` | `push   eax` | `0xffffcd10` -> `0xffffcd0c` | -4 | Move ESP down 4 bytes and store all four bytes of EAX. |
| `0x0804900b` | `push   ebx` | `0xffffcd0c` -> `0xffffcd08` | -8 | Move ESP down another 4 bytes and store all four bytes of EBX, including two zero high bytes. |
| `0x0804900c` | `nop` | `0xffffcd08` -> `0xffffcd08` | -8 | Inspect the two dwords: 0x1234 first, then 0x11223344. |
| `0x0804900d` | `pop    ebx` | `0xffffcd08` -> `0xffffcd0c` | -4 | Pop the top dword into EBX and advance ESP by 4. |
| `0x0804900e` | `pop    eax` | `0xffffcd0c` -> `0xffffcd10` | 0 | Pop the next dword into EAX and advance ESP by 4; both values and the entry ESP are restored. |
| `0x0804900f` | `mov    eax,0x1` | `0xffffcd10` -> `0xffffcd10` | 0 | Replace EAX with the i386 exit syscall number 1. |
| `0x08049014` | `xor    ebx,ebx` | `0xffffcd10` -> `0xffffcd10` | 0 | Replace EBX with exit status 0, overwriting the restored 0x1234. |
| `0x08049016` | `int    0x80` | `0xffffcd10` -> process exits | No next user state | Enter the kernel using int 0x80 and exit successfully. |

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x0804900c`. `ESP = 0xffffcd08` (S-8).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0xffffcd08` | -8 | `0x00001234` | most recently pushed register value |
| `0xffffcd0c` | -4 | `0x11223344` | first pushed register value |

The relevant bytes beginning at `ESP` are:

```text
34 12 00 00  44 33 22 11
```

The first 4 bytes encode `0x1234`; the next 4 encode `0x11223344`. Each integer is stored in **little-endian** order, least significant byte first. Byte order within a value and last-in, first-out order between stack slots are separate properties.

Even though `0x1234` fits in two bytes, `push ebx` stores **4 bytes**, because the operand is a 32-bit register. The maximum stack depth is **8 bytes** below S. The two pops restore both register values and return `ESP` to S; there are no function calls or local frame allocations.

Immediately after `pop eax`, EAX is `0x11223344` and EBX is `0x1234`. Exit setup then overwrites EAX with 1 and EBX with 0. Inspect the restored patterns before those exit instructions.

## Actual Pwndbg observation

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $esp 4
00:0000│ esp 0xffffcd08 ◂— 0x1234
01:0004│     0xffffcd0c ◂— 0x11223344
02:0008│     0xffffcd10 ◂— 1
03:000c│     0xffffcd14 —▸ 0xffffce72 ◂— '/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/build/07_stack/verified/06'
```

Immediately before the exit instruction, `ESP` was `0xffffcd10`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf32 -g -F dwarf 07_stack/06.asm -o build/07_stack/verified/06.o
ld -m elf_i386 build/07_stack/verified/06.o -o build/07_stack/verified/06
./build/07_stack/verified/06
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/06
```

Inside Pwndbg:

```text
set pagination off
set disable-randomization on
starti
info registers esp ebp
telescope $esp 4
si
```

Repeat `si` to execute **one instruction**, then inspect registers and `telescope $esp 4` again. Stop before the `nop` to compare the memory table. Use `si` through `call` to enter the function where applicable; `ni` would skip its internal stack operations. `x/16bx $esp` shows raw bytes. After checking the final restored state, `continue` finishes the process.
