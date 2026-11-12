# 04.asm - A 32-bit function frame with two local values

[Assembly source](04.asm) | [Actual Pwndbg transcript](docs/04/pwndbg.txt) | [All stack examples](README.md)

## What the program does

The program calls `work`, creates a 32-bit stack frame, and stores 100 and 200 in two local variables. It loads them into EAX and EBX, releases the locals, restores EBP, and returns to `_start`. It exits with status 0 and prints nothing.

The addresses below are from the Pwndbg trace. Let **S = 0xffffcd10**, the value of `ESP` at the first instruction of `_start`. Absolute addresses can vary between runs; offsets from S show how far the stack pointer moves.

## From process entry to exit

Linux has already prepared an initial process stack before `_start`: at S, the observed argument count was `1`; above it are argument pointers, the argument terminator, environment pointers, and the auxiliary vector. The stack is therefore not empty at entry. `_start` has no caller return address to consume with `ret`. This program exits with a Linux system call.

The stack grows toward lower addresses. In this program, a register `push` subtracts **4 bytes** from `ESP` before storing its value; `pop` reads at the current top and then adds **4 bytes**. The pointer marks the current top of the active stack, not the last unused byte.

Each row gives `ESP` **before -> after** the named instruction. All values and instruction addresses come from the linked Pwndbg run; the explanations describe what the instruction does.

| Instruction address | Instruction (Pwndbg) | ESP before -> after | Offset from S after | What happens |
|---|---|---|---|---|
| `0x08049000` | `call   0x804900e <work>` | `0xffffcd10` -> `0xffffcd0c` | -4 | Push the next instruction address as a 4-byte return address and jump to work. |
| `0x0804900e` | `push   ebp` | `0xffffcd0c` -> `0xffffcd08` | -8 | Push the incoming EBP as a 4-byte saved frame pointer. |
| `0x0804900f` | `mov    ebp,esp` | `0xffffcd08` -> `0xffffcd08` | -8 | Set EBP=ESP to anchor the frame without changing ESP. |
| `0x08049011` | `sub    esp,0x8` | `0xffffcd08` -> `0xffffcd00` | -16 | Reserve 8 bytes for two dword locals; ESP moves down, but the slots are not initialized yet. |
| `0x08049014` | `mov    DWORD PTR [ebp-0x4],0x64` | `0xffffcd00` -> `0xffffcd00` | -16 | Store decimal 100 in [EBP-4] without changing ESP. |
| `0x0804901b` | `mov    DWORD PTR [ebp-0x8],0xc8` | `0xffffcd00` -> `0xffffcd00` | -16 | Store decimal 200 in [EBP-8] without changing ESP. |
| `0x08049022` | `mov    eax,DWORD PTR [ebp-0x4]` | `0xffffcd00` -> `0xffffcd00` | -16 | Load the first local into EAX=100; this is a read, not a pop. |
| `0x08049025` | `mov    ebx,DWORD PTR [ebp-0x8]` | `0xffffcd00` -> `0xffffcd00` | -16 | Load the second local into EBX=200; both locals remain allocated. |
| `0x08049028` | `nop` | `0xffffcd00` -> `0xffffcd00` | -16 | Inspect 200, 100, saved EBP, and the return address as four consecutive dwords. |
| `0x08049029` | `mov    esp,ebp` | `0xffffcd00` -> `0xffffcd08` | -8 | Set ESP=EBP, releasing both local slots at once. |
| `0x0804902b` | `pop    ebp` | `0xffffcd08` -> `0xffffcd0c` | -4 | Pop the saved frame pointer into EBP and advance ESP by 4. |
| `0x0804902c` | `ret` | `0xffffcd0c` -> `0xffffcd10` | 0 | Pop the return address into EIP and advance ESP by 4, returning to _start. |
| `0x08049005` | `mov    eax,0x1` | `0xffffcd10` -> `0xffffcd10` | 0 | Replace EAX=100 with the i386 exit syscall number 1. |
| `0x0804900a` | `xor    ebx,ebx` | `0xffffcd10` -> `0xffffcd10` | 0 | Replace EBX=200 with exit status 0. |
| `0x0804900c` | `int    0x80` | `0xffffcd10` -> process exits | No next user state | Enter the kernel through int 0x80 and terminate successfully. |

## Stack memory at the inspection point

This is immediately before the first `nop`, at `0x08049028`. `ESP = 0xffffcd00` (S-16).

| Address | Offset from S | Stored value | Meaning |
|---|---|---|---|
| `0xffffcd00` | -16 | `0x000000c8` | local 200 |
| `0xffffcd04` | -12 | `0x00000064` | local 100 |
| `0xffffcd08` | -8 | `0x00000000` | saved EBP |
| `0xffffcd0c` | -4 | `0x08049005` | return address to _start |

The frame base is `EBP = 0xffffcd08` (S-8). `[EBP]` is the saved frame pointer, and the return address is 4 bytes above it. The locals are 4 and 8 bytes below the frame base. At maximum depth, the program uses **16 bytes below S**: return address + saved frame pointer + two locals.

The observed incoming `EBP` was `0x00000000`. Its saved slot contains that same value, and `pop ebp` restores it. Neither the two local stores nor the two loads changes `ESP`; `sub esp, 8` already allocated their space. At `nop`, **EAX=100 and EBX=200**.

The epilogue is ordered deliberately: `mov esp, ebp` releases the locals; `pop ebp` restores the old frame pointer; `ret` consumes the return address. Immediately before `ret`, `ESP` points to that return address, rather than to a local or the saved frame pointer. After `ret`, `ESP=S` and execution resumes after `call work`. Releasing stack space does not zero it.

The calculation values are visible inside `work`; exit setup later changes EAX to 1 and EBX to 0. In this 32-bit program EBX carries the exit status.

## Actual Pwndbg observation

The transcript contains registers, `telescope`, and byte-level memory before every instruction. This excerpt is the Pwndbg stack display at the inspection point above:

```text
(pwndbg) telescope $esp 4
00:0000│ esp 0xffffcd00 ◂— 0xc8
01:0004│-004 0xffffcd04 ◂— 0x64 /* 'd' */
02:0008│ ebp 0xffffcd08 ◂— 0
03:000c│+004 0xffffcd0c —▸ 0x8049005 (_start+5) ◂— mov eax, 1
```

Immediately before the exit instruction, `ESP` was `0xffffcd10`: the original S. The process exited with status 0.

## Build and step through the program

From the repository root in a Linux or WSL shell:

```bash
mkdir -p build/07_stack/verified
nasm -f elf32 -g -F dwarf 07_stack/04.asm -o build/07_stack/verified/04.o
ld -m elf_i386 build/07_stack/verified/04.o -o build/07_stack/verified/04
./build/07_stack/verified/04
echo "$?"  # observed: 0
gdb -q build/07_stack/verified/04
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
