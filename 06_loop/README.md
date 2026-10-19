# Loops

All six programs were assembled, linked, executed, and inspected with pwndbg in Kali WSL2 (`kali-linux`) on 16 October 2026. These are 64-bit Linux programs. **Every program prints output.** Four exit successfully, while two keep printing until interrupted.

## Build and run

Run these Bash commands from the repository root inside Kali WSL:

```bash
for src in 06_loop/*.asm; do
    name=$(basename "$src" .asm)
    nasm -f elf64 -g -F dwarf "$src" -o "06_loop/$name.o"
    ld -m elf_x86_64 "06_loop/$name.o" -o "06_loop/$name"
done

timeout 0.2s ./06_loop/01_loop_instruction | head -n 5
./06_loop/02_dec_jnz
./06_loop/04_while_loop
./06_loop/07_sum_loop
timeout 0.2s ./06_loop/08_infinite_loop | head -n 5
./06_loop/09_loop_syscall
```

`head` limits the displayed preview and can close the pipe before the timeout, causing `SIGPIPE`. To verify a timeout status without flooding the terminal, use:

```bash
timeout 0.2s ./06_loop/01_loop_instruction >/dev/null
echo $?  # 124: stopped by timeout
timeout 0.2s ./06_loop/08_infinite_loop >/dev/null
echo $?  # 124
```

Executables and object files are beside the `.asm` sources in `06_loop/`. Object files are ignored by Git. The sources were tested as supplied. NASM warned about implicit absolute addressing in `04_while_loop.asm` and `07_sum_loop.asm`; assembly succeeded. The linker warning for `08_infinite_loop.asm` is explained below.

## Observed output

The verification run captured standard output directly and used a 0.2-second timeout, without piping to `head`.

| Program | Standard output | Result |
|---|---|---|
| `01_loop_instruction.asm` | `Hello, Assembly!` plus newline, repeatedly | Timeout, status `124`; counter is overwritten |
| `02_dec_jnz.asm` | `Hello, Assembly!` plus newline, exactly five times (85 bytes) | Exit `0` |
| `04_while_loop.asm` | `1`, `2`, `3`, `4`, `5`, each on its own line (10 bytes) | Exit `0` |
| `07_sum_loop.asm` | `Sum = 15` plus newline (9 bytes) | Exit `0` |
| `08_infinite_loop.asm` | `Running...` plus newline, repeatedly | Timeout, status `124`; unconditional loop |
| `09_loop_syscall.asm` | `Hello, Assembly!` plus newline, exactly five times (85 bytes) | Exit `0` |

Printing uses `RAX = 1` (`write`), `RDI = 1` (standard output), `RSI` pointing to the buffer, and `RDX` giving its byte length, followed by `syscall`. Finite programs exit using `RAX = 60` (`exit`), `RDI = 0`, and `syscall`.

## Using pwndbg

```bash
pwndbg -q 06_loop/01_loop_instruction
```

The standalone launcher in this installation is `/home/kaude37/.local/bin/pwndbg` if it is not on `PATH`.

```text
pwndbg> starti
pwndbg> disassemble _start
pwndbg> disassemble repeat
pwndbg> x/8i $pc
pwndbg> si
pwndbg> info registers rcx r12 r13 eflags
```

`si` executes one machine instruction; `x/i $pc` shows the next instruction. Set a breakpoint before continuing an infinite program. Ctrl+C interrupts the running program; `kill` ends it.

Addresses below are from the build commands above. Check your disassembly before using them because source or build changes can move instructions. Register excerpts are shortened from actual sessions.

## 01: `loop` with an unprotected counter

```asm
mov rcx, 5
repeat:
    ; prepare write arguments
    syscall
    loop repeat
```

In this 64-bit program, `loop` decrements `RCX` and jumps if it is nonzero. It does not change arithmetic flags or test `ZF`.

The problem is that `syscall` clobbers `RCX` and `R11`. `RCX` receives the return instruction address, replacing the intended count of five. A breakpoint just after the syscall confirmed this:

```text
pwndbg> break *0x401020
pwndbg> run
Hello, Assembly!
pwndbg> info registers rcx rip
rcx            0x401020
rip            0x401020
```

`loop` now decrements an address, and each subsequent write overwrites the counter again. The program keeps printing instead of stopping after five lines. Single-stepping through this syscall on this WSL setup showed a different non-counter value (`0x401004`); running to the breakpoint above showed the return address directly. Both observations confirm loss of the counter. Program `09` preserves `RCX`, while program `02` uses `R12`.

## 02: `dec` and `jnz`

```asm
mov r12, 5
repeat:
    ; write the message
    dec r12
    jnz repeat
```

`dec r12` subtracts one and updates flags, including `ZF`, while preserving `CF`. `jnz` (also shown as `jne` in disassembly) jumps when `ZF = 0`. `R12` retains the count across these direct Linux system calls.

At `0x401024`, immediately before `jnz`, pwndbg showed:

| Iteration | R12 after `dec` | EFLAGS | Branch |
|---|---|---|---|
| First | `4` | `0x202 [ IF ]` | Taken |
| Fifth | `0` | `0x246 [ PF ZF IF ]` | Not taken; exit |

Reproduce with `break *0x401024`, `run`, and `info registers r12 eflags`. After the first hit, `ignore 1 3` and `continue` skip three hits and stop on the fifth iteration.

## 04: A while loop with `cmp` and `jl`

`R12` starts at one. The initial `jmp check_condition` checks the condition before entering the body. `cmp r12, 6` updates flags as if subtracting six, without storing the subtraction result. `jl loop_body` takes a signed less-than branch when `SF != OF`.

The body copies the counter to `RAX`, adds ASCII `'0'` to `AL`, stores the byte in `digit`, writes it and a newline, then executes `inc r12`. This one-byte conversion works for the values one through five used here.

At `0x401051`, immediately after the comparison:

| R12 | EFLAGS | Meaning |
|---|---|---|
| `1` | `0x293 [ CF AF SF IF ]` | `1 < 6`; enter body |
| `6` | `0x246 [ PF ZF IF ]` | Equal; leave loop |

Use `break *0x401051`, `run`, and `info registers r12 eflags`. From the first hit, `ignore 1 4` and `continue` stop at the final comparison. The observed output was:

```text
1
2
3
4
5
```

## 07: Summation and decimal conversion

`R12` holds the next number and `R13` accumulates the total. Each iteration executes `add r13, r12`, `inc r12`, `cmp r12, 6`, and `jl sum_loop`. The additions give `1 + 2 + 3 + 4 + 5 = 15`.

Observed in pwndbg:

```text
pwndbg> break *0x401018
pwndbg> run
pwndbg> info registers r12 r13
r12            0x6
r13            0xf

pwndbg> break *0x401026
pwndbg> continue
pwndbg> info registers rax rdx
rax            0x1
rdx            0x5

pwndbg> break *0x401039
pwndbg> continue
pwndbg> x/2bx &result
0x402008 <result>:  0x31  0x35
```

The first breakpoint is after the sum loop. The second is just after `div rbx`: clearing `RDX` beforehand makes the unsigned dividend `RDX:RAX` equal to 15; division by ten gives quotient one in `RAX` and remainder five in `RDX`. Adding `'0'` converts them to ASCII `'1'` and `'5'`, observed at the third breakpoint after both stores. Arithmetic flags after `DIV` are undefined; inspect its results in registers.

The program printed `Sum = 15`, but `result resb 1` reserves only one byte while the code stores and prints two bytes, including `result + 1`. The second store is outside the declared buffer. Reserving two bytes (`result resb 2`) is the appropriate correction; successful output does not make the current reservation correct. This conversion also assumes a two-digit result.

## 08: An unconditional infinite loop

The body writes `Running...` and executes `jmp repeat`. There is no counter, condition, or exit syscall. Stepping the jump at `0x40101b` returned `RIP` to `0x401000 <repeat>`.

The file declares `global _start` but never defines an `_start:` label. The linker reported:

```text
warning: cannot find entry symbol _start; defaulting to 0000000000401000
```

That fallback is the address of `repeat` in this build, so the program still runs. Defining `_start:` immediately before `repeat:` would provide an explicit entry point and remove the warning.

Use `starti` and `x/6i $pc` rather than `disassemble _start` here, since `_start` is not defined. Step five instructions to reach the jump, then one more to see control return to `repeat`.

## 09: Preserve `RCX` across `syscall`

```asm
mov rcx, 5
repeat:
    push rcx
    ; prepare write arguments
    syscall
    pop rcx
    loop repeat
```

`push rcx` saves the count on the stack before the syscall. `pop rcx` restores it afterward so `loop` can count down normally. Each iteration balances its push and pop.

At the first syscall (`0x40101f`), `RCX` was five and `x/gx $rsp` showed the saved value `0x0000000000000005`. After the syscall clobbered `RCX`, stepping `pop rcx` restored five. Stepping `loop` changed it to four and returned to `repeat`. The complete run printed exactly five lines and exited with status `0`.

Reproduce with `break *0x40101f`, `run`, `info registers rcx rsp`, and `x/gx $rsp`. Then use `si` and `info registers rcx` after each of the syscall, pop, and loop instructions.
