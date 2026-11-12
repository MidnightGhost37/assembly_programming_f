# 02.asm - A 64-bit function frame with two local values

[Assembly source](02.asm) | [Actual Pwndbg transcript](docs/02/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program calls `work`, creates a 64-bit stack frame, and stores 100 and 200 in two local variables. It loads them into RAX and RBX, releases the locals, restores RBP, and returns to `_start`. It exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0x00007fffffffdbe0**, the value of `RSP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **8 bytes** from `RSP` before storing its value; `pop` reads at the current top and then adds **8 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `RSP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | RSP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x0000000000401000` | `call   0x40100f <work>` | `0x00007fffffffdbe0` -> `0x00007fffffffdbd8` | -8 | Push the address of the next instruction as an 8-byte return address, then jump to work. |
| `0x000000000040100f` | `push   rbp` | `0x00007fffffffdbd8` -> `0x00007fffffffdbd0` | -16 | Push the incoming RBP as an 8-byte saved frame pointer. |
| `0x0000000000401010` | `mov    rbp,rsp` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd0` | -16 | Copy RSP into RBP to establish a stable frame base; no push occurs. |
| `0x0000000000401013` | `sub    rsp,0x10` | `0x00007fffffffdbd0` -> `0x00007fffffffdbc0` | -32 | Reserve 16 bytes for two qword locals by moving RSP down; allocation alone does not initialize memory. |
| `0x0000000000401017` | `mov    QWORD PTR [rbp-0x8],0x64` | `0x00007fffffffdbc0` -> `0x00007fffffffdbc0` | -32 | Store 100 at [RBP-8]. This writes a local slot without changing RSP. |
| `0x000000000040101f` | `mov    QWORD PTR [rbp-0x10],0xc8` | `0x00007fffffffdbc0` -> `0x00007fffffffdbc0` | -32 | Store 200 at [RBP-16], the current top of the allocated frame; RSP is unchanged. |
| `0x0000000000401027` | `mov    rax,QWORD PTR [rbp-0x8]` | `0x00007fffffffdbc0` -> `0x00007fffffffdbc0` | -32 | Load the first local (100) into RAX; reading memory does not pop it. |
| `0x000000000040102b` | `mov    rbx,QWORD PTR [rbp-0x10]` | `0x00007fffffffdbc0` -> `0x00007fffffffdbc0` | -32 | Load the second local (200) into RBX; RSP remains fixed. |
| `0x000000000040102f` | `nop` | `0x00007fffffffdbc0` -> `0x00007fffffffdbc0` | -32 | Inspect locals 200 and 100, saved RBP, and the return address in ascending address order. |
| `0x0000000000401030` | `mov    rsp,rbp` | `0x00007fffffffdbc0` -> `0x00007fffffffdbd0` | -16 | Restore RSP from RBP, discarding the 16-byte local allocation in one operation. |
| `0x0000000000401033` | `pop    rbp` | `0x00007fffffffdbd0` -> `0x00007fffffffdbd8` | -8 | Restore the incoming RBP from [RSP] and advance RSP by 8. |
| `0x0000000000401034` | `ret` | `0x00007fffffffdbd8` -> `0x00007fffffffdbe0` | 0 | Load the saved return address into RIP and advance RSP by 8; resume in _start. |
| `0x0000000000401005` | `mov    eax,0x3c` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Replace RAX=100 with the exit syscall number 60. |
| `0x000000000040100a` | `xor    rdi,rdi` | `0x00007fffffffdbe0` -> `0x00007fffffffdbe0` | 0 | Set RDI=0 for successful exit, leaving RBX=200. |
| `0x000000000040100d` | `syscall` | `0x00007fffffffdbe0` -> process exits | No next user state | Terminate through the kernel with status 0. |

NASM may encode a source instruction such as `mov rax, 60` as `mov eax, 0x3c`. Writing EAX clears the upper half of RAX, so the observed instruction still sets RAX to 60. The table retains the actual disassembly.

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x000000000040102f`. `RSP = 0x00007fffffffdbc0` (S-32).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0x00007fffffffdbc0` | -32 | `0x00000000000000c8` | local 200 |
| `0x00007fffffffdbc8` | -24 | `0x0000000000000064` | local 100 |
| `0x00007fffffffdbd0` | -16 | `0x0000000000000000` | saved RBP |
| `0x00007fffffffdbd8` | -8 | `0x0000000000401005` | return address to _start |

The frame base is `RBP = 0x00007fffffffdbd0` (S-16). `[RBP]` is the saved frame pointer, and the return address is 8 bytes above it. The locals are 8 and 16 bytes below the frame base. At maximum depth, the program uses **32 bytes below S**: return address + saved frame pointer + two locals.

The observed incoming `RBP` was `0x0000000000000000`. Its saved slot contains that same value, and `pop rbp` restores it. Neither the two local stores nor the two loads changes `RSP`; `sub rsp, 16` already allocated their space. At `nop`, **RAX=100 and RBX=200**.

The epilogue is ordered deliberately: `mov rsp, rbp` releases the locals; `pop rbp` restores the old frame pointer; `ret` consumes the return address. Immediately before `ret`, `RSP` points to that return address, rather than to a local or the saved frame pointer. After `ret`, `RSP=S` and execution resumes after `call work`. Releasing stack space does not zero it.

The calculation values are visible inside `work`; exit setup later changes RAX to 60 while RBX remains 200. RDI carries the exit status.

## Actual Pwndbg observation

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $rsp 4
00:0000│ rsp 0x7fffffffdbc0 ◂— 0xc8
01:0008│-008 0x7fffffffdbc8 ◂— 0x64 /* 'd' */
02:0010│ rbp 0x7fffffffdbd0 ◂— 0
03:0018│+008 0x7fffffffdbd8 —▸ 0x401005 (_start+5) ◂— mov eax, 0x3c
```

Immediately before the exit instruction, `RSP` was `0x00007fffffffdbe0`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf64 -g -F dwarf 07_stack/02.asm -o build/07_stack/verified/02.o
ld -m elf_x86_64 build/07_stack/verified/02.o -o build/07_stack/verified/02
./build/07_stack/verified/02
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/02
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
