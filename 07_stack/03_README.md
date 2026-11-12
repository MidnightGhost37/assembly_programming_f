# 03.asm - The hidden push and pop in call and ret

[Assembly source](03.asm) | [Actual Pwndbg transcript](docs/03/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program starts with RAX=10 and calls `calculate`, which adds 5. The call stores a return address on the stack; `ret` consumes it and returns with RAX=15. Exit setup then replaces RAX with 60. The program exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0x00007fffffffdbe0**, the value of `RSP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **8 bytes** from `RSP` before storing its value; `pop` reads at the current top and then adds **8 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `RSP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | RSP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x0000000000401000` | `mov    eax,0xa` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Initialize the calculation input RAX=10 without changing RSP. |
| `0x0000000000401005` | `call   0x401015 <calculate>` | `0x00007fffffffdbe0` -> `0x00007fffffffdbd8` | -8 | Push the 8-byte address of after_call, then transfer control to calculate. |
| `0x0000000000401015` | `add    rax,0x5` | `0x00007fffffffdbd8` -> `0x00007fffffffdbd8` | -8 | Add 5 to RAX, producing 15; the return address stays at [RSP]. |
| `0x0000000000401019` | `ret` | `0x00007fffffffdbd8` -> `0x00007fffffffdbe0` | 0 | Read the return address into RIP and advance RSP by 8; control reaches after_call. |
| `0x000000000040100a` | `nop` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Observe RAX=15 and the original RSP; this is the calculation result before exit setup. |
| `0x000000000040100b` | `mov    eax,0x3c` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Replace the result 15 with exit syscall number 60. |
| `0x0000000000401010` | `xor    rdi,rdi` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Set exit status RDI=0. |
| `0x0000000000401013` | `syscall` | `0x00007fffffffdbe0` -> process exits | No next user state | Terminate successfully; this does not return from _start with ret. |

NASM may encode a source instruction such as `mov rax, 60` as `mov eax, 0x3c`. Writing EAX clears the upper half of RAX, so the observed instruction still sets RAX to 60. The table retains the actual disassembly.

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x000000000040100a`. `RSP = 0x00007fffffffdbe0` (S+0).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0x00007fffffffdbe0` | +0 | `0x0000000000000001` | initial argc, now visible again after ret |

At entry to `calculate`, RSP was `0x00007fffffffdbd8` (S-8) and `[RSP]` was `0x000000000040100a`, the address of `after_call`. `call` stored the address following the call, rather than the function address. `add rax, 5` changes RAX from 10 to 15 without touching that stack slot.

`ret` then reads `0x000000000040100a` into RIP and advances RSP to S. The `nop` shown above is **after** the return, so the return-address slot is no longer active. There is no explicit `push` or `pop` in this source, but the call/return pair still uses 8 stack bytes. There is no frame pointer setup and no local stack allocation.

The observed result is **RAX=15 (`0xf`) at `after_call`**. It is not the process exit status: `mov rax, 60` replaces it, and RDI=0 requests a successful exit.

## Actual Pwndbg observation

At entry to `calculate`, the actual Pwndbg display shows the return address at the top of the stack:

```text
(pwndbg) telescope $rsp 4
00:0000│ rsp 0x7fffffffdbd8 —▸ 0x40100a (after_call) ◂— nop 
01:0008│     0x7fffffffdbe0 ◂— 1
02:0010│     0x7fffffffdbe8 —▸ 0x7fffffffde72 ◂— '/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/build/07_stack/verified/03'
03:0018│     0x7fffffffdbf0 ◂— 0
```

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $rsp 4
00:0000│ rsp 0x7fffffffdbe0 ◂— 1
01:0008│     0x7fffffffdbe8 —▸ 0x7fffffffde72 ◂— '/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/build/07_stack/verified/03'
02:0010│     0x7fffffffdbf0 ◂— 0
03:0018│     0x7fffffffdbf8 —▸ 0x7fffffffded1 ◂— 'SHELL=/usr/bin/zsh'
```

Immediately before the exit instruction, `RSP` was `0x00007fffffffdbe0`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf64 -g -F dwarf 07_stack/03.asm -o build/07_stack/verified/03.o
ld -m elf_x86_64 build/07_stack/verified/03.o -o build/07_stack/verified/03
./build/07_stack/verified/03
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/03
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
