# 07 - The stack: predict, step, explain

## Stack examples

Each guide explains execution from `_start` to exit, including stack operations, register values, and observations from Pwndbg.

| Source | Separate README | Focus |
|---|---|---|
| [01.asm](01.asm) | [01 guide](01_README.md) | Two pushes and pops into different registers |
| [02.asm](02.asm) | [02 guide](02_README.md) | 64-bit function frame and local variables |
| [03.asm](03.asm) | [03 guide](03_README.md) | Return address stored by `call` and consumed by `ret` |
| [04.asm](04.asm) | [04 guide](04_README.md) | 32-bit function frame and local variables |
| [05.asm](05.asm) | [05 guide](05_README.md) | 8-byte stack slots and little-endian storage |
| [06.asm](06.asm) | [06 guide](06_README.md) | 4-byte stack slots and little-endian storage |

Run `python3 07_stack/verify_stack.py` from the repository root in WSL to rebuild and check all six programs with Pwndbg. All six programs exit with status 0 and produce no terminal output.

**Virtual-class mission:** run every program, pause at the interesting instruction, and explain what changed in registers and memory. These examples produce **no terminal output**; the evidence is in GDB. Bring one question or a changed version of a program to discuss.

The stack grows toward lower addresses. On x86-64, `push` subtracts 8 from `RSP` and stores an 8-byte value; `pop` loads from `[RSP]` and adds 8. In 32-bit mode, the corresponding changes to `ESP` are 4 bytes. `call` pushes a return address, and `ret` pops it into the instruction pointer. A stack frame gives a function stable offsets from `RBP` or `EBP` for local values.

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

## A debugger routine for every example

```bash
gdb -q 07_stack/01
```

At the `(gdb)` prompt (the same commands work in pwndbg):

```text
set disassembly-flavor intel
break _start
run
display/i $pc
info registers rsp rax rbx rcx rdx
x/4gx $rsp
si
```

Use `si` to execute one instruction, then repeat `info registers` and `x/4gx $rsp`. The displayed instruction is the **next** instruction, so inspect registers after stepping past a `push`, `pop`, `call`, or `ret`. For the 32-bit examples use `info registers esp eax ebx ebp` and `x/4wx $esp` (`w` means four-byte words). `quit` leaves GDB. Addresses vary by build and system, so use source labels and register-relative addresses instead of copying absolute addresses.

Before each run, write down your prediction. Then compare it with the debugger.

| Program | Stop and inspect | Predict before stepping | Explain after stepping |
|---|---|---|---|
| [01.asm](01.asm) | The two `nop` instructions | What are `RCX`, `RDX`, and the change in `RSP` after two pushes and two pops? | Why does the first `pop` receive `200` rather than `100`? |
| [02.asm](02.asm) | `nop` inside `work`, then `ret` | Where are `100`, `200`, and the return address relative to `RBP`? | Why does restoring `RSP` and `RBP` make `ret` safe? |
| [03.asm](03.asm) | `after_call` | What will `RAX` contain after `calculate`? | What address did `call` place on the stack? |
| [04.asm](04.asm) | `nop` inside `work` | How do the local offsets and stack changes differ from `02`? | Which 32-bit instruction returns to `_start`? |
| [05.asm](05.asm) | Each `nop` | Do `RAX` and `RBX` regain their original hexadecimal values? | Why can `push`/`pop` preserve full register values? |
| [06.asm](06.asm) | Its `nop` | How many bytes does each push reserve here? | What would go wrong if the pops were reversed? |

### 01 and 05: last in, first out

In `01`, `RAX=100` is pushed first and `RBX=200` second. At the first `nop`, the top two eight-byte stack slots hold `200` and `100`. The next `pop rcx` takes `200`, and `pop rdx` takes `100`. At the second `nop`, `RSP` has returned to its original value. `05` repeats the idea with larger hexadecimal values and pops into the original registers.

**Try it:** swap the two `pop` destinations in `01`, rebuild, and predict both final registers. Then add one extra `push rax` without a matching `pop`. What happens to `RSP`? Restore the file after the experiment if you want to keep the original example.

### 02 and 04: function frames

The `call work` instruction puts a return address on the stack. Inside `work`, `push rbp`/`push ebp` saves the caller's frame pointer. `mov rbp, rsp` or `mov ebp, esp` establishes a reference point; `sub rsp, 16` or `sub esp, 8` reserves two local slots. The first local is at `[rbp-8]` or `[ebp-4]`, the second at `[rbp-16]` or `[ebp-8]`.

Try this inside `02` at its `nop`:

```text
info registers rbp rsp rax rbx
x/4gx $rbp-16
x/gx $rbp+8
```

In `04`, use `x/4wx $ebp-8` and `x/wx $ebp+4`. The positive offset points at the return address in each program. `mov rsp, rbp`/`mov esp, ebp` discards the local allocation, `pop rbp`/`pop ebp` restores the saved frame pointer, and `ret` uses the return address.

**Discuss:** `02` and `04` load their second local into `RBX`/`EBX` but do not save and restore that register. If `work` were called by a larger program that expected `RBX` preserved, what change would you make? Account for the shifted offsets if you add another push.

### 03: `call` and `ret` without a frame

`03` passes `10` in `RAX`; `calculate` adds `5` and returns. Stop at `after_call` and check that `RAX=15`. This small function needs no local stack space or frame pointer. Step into `call` to see `RSP` decrease by eight and the return address appear at the top; step over `ret` to see `RSP` restored.

**Try it:** change `add rax, 5` to `add rax, 20`. Predict the result before running. Then explain why the final shell exit status is still `0`: `_start` later replaces `RAX` with the exit syscall number and clears `RDI`.

## Worked trace: `01.asm` - two pushes, two pops

The important part of the program is short enough to trace instruction by instruction:

```asm
mov rax, 100
mov rbx, 200
push rax
push rbx
nop
pop rcx
pop rdx
nop
```

Let `S` be the value of `RSP` just before `push rax`. Stack addresses below are relative to `S`, so your machine does not need to show the same absolute address.

| After instruction | `RSP` | Top stack slot | `RCX` | `RDX` |
|---|---:|---:|---:|---:|
| `mov rbx, 200` | `S` | Earlier process data | Unchanged | Unchanged |
| `push rax` | `S - 8` | `100` | Unchanged | Unchanged |
| `push rbx` | `S - 16` | `200` | Unchanged | Unchanged |
| `pop rcx` | `S - 8` | `100` | `200` | Unchanged |
| `pop rdx` | `S` | Earlier process data | `200` | `100` |

`nop` means *no operation*. It is a convenient place to stop: the first one is after the pushes, and the second is after the pops. `pop` changes the stack pointer; it does not erase the old memory bytes. You may still see `100` or `200` below `RSP` afterward, but those slots are no longer part of the active stack.

At the first `nop`, use `x/2gx $rsp`. Before the second `nop`, step past both pops and use `info registers rcx rdx rsp`. Record the value of `RSP` before the first push so you can check that it returns to the same value.

**Live question:** if `pop rcx` were replaced by `pop rax`, what would happen to `RAX`? Would the values still leave the stack in the same order?

## Worked trace: `02.asm` - a 64-bit stack frame

The `work` procedure makes room for two local 64-bit values:

```asm
work:
    push rbp
    mov rbp, rsp
    sub rsp, 16
    mov qword [rbp - 8], 100
    mov qword [rbp - 16], 200
    mov rax, [rbp - 8]
    mov rbx, [rbp - 16]
    nop
    mov rsp, rbp
    pop rbp
    ret
```

Let `F` be `RBP` after `mov rbp, rsp`. At the `nop`, the stack layout is:

```text
Higher addresses
F + 8   return address pushed by call work
F + 0   caller's saved RBP
F - 8   local value 100                 <- RAX reads here
F - 16  local value 200                 <- RBX reads here; RSP here
Lower addresses
```

`sub rsp, 16` reserves space; it does **not** initialize those bytes. The two `mov qword` instructions write the values. `RBP` remains steady while `RSP` can move. At the `nop`, `RAX=100`, `RBX=200`, and `RSP=RBP-16`.

Walk through the epilogue carefully. `mov rsp, rbp` moves past both locals. `pop rbp` restores the caller's saved frame pointer and moves `RSP` to the return address. `ret` pops that address and resumes in `_start`, immediately after `call work`. To see that destination, stop just before `ret` and compare `x/gx $rsp` with `x/i $pc` after stepping over `ret`.

**Challenge:** remove `mov rsp, rbp` in a temporary copy. Predict which value `pop rbp` will take and what `ret` will use as an address. Run only under GDB and explain the failure. Restore the correct epilogue afterward.

## Worked trace: `03.asm` - the return address is enough

There is no `push rbp` and no local allocation:

```asm
mov rax, 10
call calculate
after_call:
    nop
calculate:
    add rax, 5
    ret
```

The actual source has exit instructions between `after_call` and `calculate`; execution reaches `calculate` through `call`, then returns to `after_call`. If `RSP=S` before `call`, it is `S-8` inside `calculate` and returns to `S` after `ret`. `RAX` changes from `10` to `15`.

Use these breakpoints to separate the two moments:

```text
break calculate
break after_call
run
info registers rax rsp
x/gx $rsp
continue
info registers rax rsp
```

The value at `[RSP]` inside `calculate` is an **address**, not the input number. Ask a classmate to identify which instruction it points to. The input and result use a register; the stack is used only for control flow in this example.

## Worked trace: `04.asm` - the same frame in 32-bit mode

`04` mirrors `02`, but uses 32-bit registers and four-byte local values. The `BITS 32` directive and the `elf32`/`elf_i386` build options are all needed. At the `nop`, let `F=EBP`:

```text
Higher addresses
F + 4   return address
F + 0   saved EBP
F - 4   local value 100                 <- EAX
F - 8   local value 200                 <- EBX; ESP here
Lower addresses
```

`push ebp` reserves four bytes and `sub esp, 8` reserves eight. Use `x/4wx $ebp-8` to inspect four consecutive four-byte words: the two locals, saved `EBP`, and return address. Compare it with `02`, where each slot occupies eight bytes.

After returning, this program exits through `mov eax, 1` and `int 0x80`, the 32-bit Linux syscall convention. The 64-bit examples put `60` in `RAX` and use `syscall`. The exit setup overwrites `EAX`, so inspect the loaded local at the `nop`, before returning.

**Live question:** what would happen if `BITS 32` instructions were placed in a 64-bit executable? NASM may still produce an object file, so inspect the output format with `file` and the instructions with `objdump -d -M intel` before assuming that a successful assembly means the program will run correctly. Explain why this example is built as `elf32` and linked with `elf_i386`.

## Worked trace: `05.asm` - preserving entire 64-bit values

`05` pushes `0x1122334455667788` from `RAX` and `0x1234` from `RBX`, then pops in reverse order. The stack holds the entire eight-byte `RAX` value. At the first `nop`:

```text
[RSP]       = 0x0000000000001234
[RSP + 8]   = 0x1122334455667788
```

At the second `nop`, `RBX=0x1234` and `RAX=0x1122334455667788`. The leading zeros on `RBX` are simply its 64-bit representation. Immediately afterward, `mov rax, 60` replaces the restored `RAX` to select the exit syscall, so pause at the second `nop` to see the result.

**Try it:** replace `pop rbx` with `pop rcx` in a temporary copy. Which register no longer gets restored? What still happens to `RSP`?

## Worked trace: `06.asm` - preserving 32-bit values

`06` uses the same pattern with `EAX=0x11223344` and `EBX=0x1234`. Each push stores **four** bytes. At its `nop`, `EAX` and `EBX` hold their original values and `ESP` is back where it started.

Compare the two programs side by side:

| Feature | `05.asm` | `06.asm` |
|---|---|---|
| Register width | 64 bits | 32 bits |
| Bytes per push/pop | 8 | 4 |
| Stack pointer | `RSP` | `ESP` |
| Memory view in GDB | `x/2gx $rsp` | `x/2wx $esp` |
| Exit mechanism | `syscall` with `RAX=60` | `int 0x80` with `EAX=1` |

**Explain to a partner:** why is the first value pushed the second value popped? Draw two boxes for the stack slots, label the top, and update the pointer after each instruction.

## Bring to the discussion

1. Sketch the stack at the first `nop` in `01` and inside `work` in `02`. Label addresses relative to `RSP` or `RBP`.
2. Show one prediction that matched and one that surprised you. Include the GDB command and observed value.
3. Why does a mismatched push/pop pair matter before `ret`? What happens if a function returns with the wrong stack pointer?
4. What changes between 64-bit and 32-bit examples besides register names?
5. Propose a tiny function that adds two numbers using either registers or stack locals. Which values must survive the call?

**Challenge:** write `07_stack/07.asm` with a function that takes two values, stores them in stack locals, returns their sum in `RAX`, and leaves `RSP` exactly as it found it. Demonstrate the result at a breakpoint before the exit syscall. Keep your source and one debugger observation ready to share.
