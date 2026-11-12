# 05.asm - 64-bit stack slots and little-endian bytes

[Assembly source](05.asm) | [Actual Pwndbg transcript](docs/05/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program pushes `0x1122334455667788` and `0x1234` as two 8-byte values, then pops them back into RBX and RAX. The register values and starting RSP are restored before exit setup. It exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0x00007fffffffdbe0**, the value of `RSP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **8 bytes** from `RSP` before storing its value; `pop` reads at the current top and then adds **8 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `RSP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | RSP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x0000000000401000` | `movabs rax,0x1122334455667788` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Load the full 64-bit pattern 0x1122334455667788 into RAX. |
| `0x000000000040100a` | `mov    ebx,0x1234` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Load RBX=0x1234; the register is still 64 bits wide. |
| `0x000000000040100f` | `push   rax` | `0x00007fffffffdbe0` -> `0x00007fffffffdbd8` | -8 | Move RSP down 8 bytes and store all eight bytes of RAX. |
| `0x0000000000401010` | `push   rbx` | `0x00007fffffffdbd8` -> `0x00007fffffffdbd0` | -16 | Move RSP down another 8 bytes and store the full RBX value, including six zero high bytes. |
| `0x0000000000401011` | `nop` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd0` | -16 | Inspect the two qwords: 0x1234 first, then 0x1122334455667788. |
| `0x0000000000401012` | `pop    rbx` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd8` | -8 | Pop the top qword back into RBX and advance RSP by 8. |
| `0x0000000000401013` | `pop    rax` | `0x00007fffffffdbd8` -> `0x00007fffffffdbe0` | 0 | Pop the next qword into RAX and advance RSP by 8, restoring both values and the original RSP. |
| `0x0000000000401014` | `mov    eax,0x3c` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Replace the restored RAX pattern with the exit syscall number 60. |
| `0x0000000000401019` | `xor    rdi,rdi` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Set RDI=0; RBX remains 0x1234. |
| `0x000000000040101c` | `syscall` | `0x00007fffffffdbe0` -> process exits | No next user state | Terminate through the x86-64 exit syscall with status 0. |

NASM may encode a source instruction such as `mov rax, 60` as `mov eax, 0x3c`. Writing EAX clears the upper half of RAX, so the observed instruction still sets RAX to 60. The table retains the actual disassembly.

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x0000000000401011`. `RSP = 0x00007fffffffdbd0` (S-16).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0x00007fffffffdbd0` | -16 | `0x0000000000001234` | most recently pushed register value |
| `0x00007fffffffdbd8` | -8 | `0x1122334455667788` | first pushed register value |

The relevant bytes beginning at `RSP` are:

```text
34 12 00 00 00 00 00 00  88 77 66 55 44 33 22 11
```

The first 8 bytes encode `0x1234`; the next 8 encode `0x1122334455667788`. Each integer is stored in **little-endian** order, least significant byte first. Byte order within a value and last-in, first-out order between stack slots are separate properties.

Even though `0x1234` fits in two bytes, `push rbx` stores **8 bytes**, because the operand is a 64-bit register. The maximum stack depth is **16 bytes** below S. The two pops restore both register values and return `RSP` to S; there are no function calls or local frame allocations.

Immediately after `pop rax`, RAX is `0x1122334455667788` and RBX is `0x1234`. Exit setup overwrites RAX with 60, but RBX remains `0x1234`; RDI=0 supplies the exit status.

## Actual Pwndbg observation

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $rsp 4
00:0000│ rsp 0x7fffffffdbd0 ◂— 0x1234
01:0008│     0x7fffffffdbd8 ◂— 0x1122334455667788
02:0010│     0x7fffffffdbe0 ◂— 1
03:0018│     0x7fffffffdbe8 —▸ 0x7fffffffde72 ◂— '/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/build/07_stack/verified/05'
```

Immediately before the exit instruction, `RSP` was `0x00007fffffffdbe0`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf64 -g -F dwarf 07_stack/05.asm -o build/07_stack/verified/05.o
ld -m elf_x86_64 build/07_stack/verified/05.o -o build/07_stack/verified/05
./build/07_stack/verified/05
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/05
```

Inside Pwndbg:

```text
set pagination off
set disable-randomization on
starti
info registers rsp rbp
telescope $rsp 4
si
```

Repeat `si` to execute **one instruction**, then inspect registers and `telescope $rsp 4` again. Stop before the `nop` to compare the memory table. Use `si` through `call` to enter the function where applicable; `ni` would skip its internal stack operations. `x/16bx $rsp` shows raw bytes. After checking the final restored state, `continue` finishes the process.
