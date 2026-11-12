# 01.asm - Two pushes, two pops: last in, first out

[Assembly source](01.asm) | [Actual Pwndbg transcript](docs/01/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program pushes 100 and 200 onto the stack, then pops them into RCX and RDX in reverse order. RCX ends up with 200, RDX with 100, and RSP returns to its starting value. It exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0x00007fffffffdbe0**, the value of `RSP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **8 bytes** from `RSP` before storing its value; `pop` reads at the current top and then adds **8 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `RSP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | RSP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x0000000000401000` | `mov    eax,0x64` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Load decimal 100 into RAX; stack memory and RSP are unchanged. |
| `0x0000000000401005` | `mov    ebx,0xc8` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Load decimal 200 into RBX; RSP is unchanged. |
| `0x000000000040100a` | `push   rax` | `0x00007fffffffdbe0` -> `0x00007fffffffdbd8` | -8 | Subtract 8 from RSP, then store the 8-byte value 100 at the new top. |
| `0x000000000040100b` | `push   rbx` | `0x00007fffffffdbd8` -> `0x00007fffffffdbd0` | -16 | Subtract another 8, then store 200 above 100 in stack order (at a lower address). |
| `0x000000000040100c` | `nop` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd0` | -16 | Pause for inspection; the top two qwords are 200, then 100. |
| `0x000000000040100d` | `pop    rcx` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd8` | -8 | Read 200 from [RSP] into RCX, then increase RSP by 8. |
| `0x000000000040100e` | `pop    rdx` | `0x00007fffffffdbd8` -> `0x00007fffffffdbe0` | 0 | Read 100 from [RSP] into RDX, then increase RSP by 8. |
| `0x000000000040100f` | `nop` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Pause with the original RSP restored; RCX=200 and RDX=100. |
| `0x0000000000401010` | `mov    eax,0x3c` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Set Linux x86-64 exit syscall number 60 in RAX, replacing 100. |
| `0x0000000000401015` | `xor    rdi,rdi` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Set exit status RDI=0; RSP does not change. |
| `0x0000000000401018` | `syscall` | `0x00007fffffffdbe0` -> process exits | No next user state | Ask the kernel to terminate the process; there is no following user instruction. |

NASM may encode a source instruction such as `mov rax, 60` as `mov eax, 0x3c`. Writing EAX clears the upper half of RAX, so the observed instruction still sets RAX to 60. The table retains the actual disassembly.

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x000000000040100c`. `RSP = 0x00007fffffffdbd0` (S-16).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0x00007fffffffdbd0` | -16 | `0x00000000000000c8` | most recently pushed register value |
| `0x00007fffffffdbd8` | -8 | `0x0000000000000064` | first pushed register value |

Although RAX was loaded first, RBX was pushed last and is popped first into RCX. The destination register does not have to match the pushed source: RCX becomes **200 (`0xc8`)**, and RDX becomes **100 (`0x64`)**. At the second `nop`, RSP equals S. The pops remove the values from the active stack; they do not erase their old bytes in memory. No function call or local frame is used.

## Actual Pwndbg observation

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $rsp 4
00:0000│ rsp 0x7fffffffdbd0 ◂— 0xc8
01:0008│     0x7fffffffdbd8 ◂— 0x64 /* 'd' */
02:0010│     0x7fffffffdbe0 ◂— 1
03:0018│     0x7fffffffdbe8 —▸ 0x7fffffffde72 ◂— '/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/build/07_stack/verified/01'
```

Immediately before the exit instruction, `RSP` was `0x00007fffffffdbe0`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf64 -g -F dwarf 07_stack/01.asm -o build/07_stack/verified/01.o
ld -m elf_x86_64 build/07_stack/verified/01.o -o build/07_stack/verified/01
./build/07_stack/verified/01
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/01
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
