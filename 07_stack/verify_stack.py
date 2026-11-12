#!/usr/bin/env python3
"""Rebuild/run all six examples, then trace and verify them in GDB + Pwndbg.

Run from WSL: python3 07_stack/verify_stack.py
Uses the user's normal GDB initialization; Pwndbg must already be configured.
"""
from pathlib import Path
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/07_stack/verified"
DOCS = ROOT / "07_stack/docs"
BITS = {"01": 64, "02": 64, "03": 64, "04": 32, "05": 64, "06": 32}


def trace():
    import gdb
    import pwndbg  # Fail explicitly if the user's Pwndbg did not load.

    gdb.execute("set pagination off")
    gdb.execute("set confirm off")
    gdb.execute("set style enabled off")
    gdb.execute("set context-sections ''")
    gdb.execute("set disable-randomization on")
    results = {}
    for name, bits in BITS.items():
        if name != os.environ["STACK_EXAMPLE"]:
            continue
        word = bits // 8
        sp, bp = ("rsp", "rbp") if bits == 64 else ("esp", "ebp")
        regs = [sp, bp] + (["rax", "rbx", "rcx", "rdx"] if bits == 64 else ["eax", "ebx", "ecx", "edx"])
        def reg(r):
            return int(gdb.parse_and_eval("$" + r)) & ((1 << bits) - 1)
        def memory(address, count=1):
            data = bytes(gdb.selected_inferior().read_memory(address, count * word))
            return [int.from_bytes(data[i:i+word], "little") for i in range(0, len(data), word)]
        lines = []
        def emit(command):
            output = gdb.execute(command, to_string=True)
            lines.append("(pwndbg) " + command + "\n" + output)
            return output
        emit("file " + str(BUILD / name))
        emit("version")
        emit("starti")
        emit("disassemble _start")
        if name in ("02", "04"):
            emit("disassemble work")
        if name == "03":
            emit("disassemble calculate")
        entry_sp, entry_bp = reg(sp), reg(bp)
        states = []
        exit_codes = []
        def on_exit(event):
            code = getattr(event, "exit_code", None)
            exit_codes.append(code)
            lines.append(f"GDB inferior exited event: exit_code={code}\n")
        gdb.events.exited.connect(on_exit)
        try:
            for step in range(40):
                pc = int(gdb.parse_and_eval("$pc"))
                decoded = gdb.selected_frame().architecture().disassemble(pc, count=2)
                instruction = decoded[0]["asm"]
                before = {r: reg(r) for r in regs}
                stack = memory(before[sp], 4)
                lines.append(f"\nSTEP {step}: {hex(pc)} {instruction}; {sp}-entry = {before[sp]-entry_sp}\n")
                emit("info registers " + " ".join(regs))
                emit("telescope $" + sp + " 4")
                emit(("x/16bx $" + sp))
                state = {"step": step, "pc": pc, "instruction": instruction,
                         "registers": before, "delta": before[sp]-entry_sp, "stack": stack}
                states.append(state)
                op = instruction.split()[0]
                if op in ("syscall", "int"):
                    assert reg("rax" if bits == 64 else "eax") == (60 if bits == 64 else 1)
                    assert reg("rdi" if bits == 64 else "ebx") == 0
                    assert before[sp] == entry_sp, "Unbalanced final stack"
                    assert before[bp] == entry_bp, "Frame pointer was not restored"
                    emit("stepi")
                    assert exit_codes == [0], f"Unexpected exit: {exit_codes}"
                    break
                expected_sp = before[sp]
                if op in ("push", "call"):
                    expected_sp -= word
                elif op in ("pop", "ret"):
                    expected_sp += word
                elif instruction.startswith("sub") and re.search(r"\b" + sp + r"\b", instruction):
                    expected_sp -= int(instruction.split(",")[-1].strip(), 0)
                elif instruction.startswith("mov") and instruction.split(None, 1)[1].replace(" ", "") == sp + "," + bp:
                    expected_sp = before[bp]
                emit("stepi")
                assert reg(sp) == expected_sp, f"Incorrect {sp} transition after {instruction}"
                if op == "push":
                    source = instruction.split()[-1]
                    assert memory(reg(sp))[0] == before[source]
                if op == "pop":
                    destination = instruction.split()[-1]
                    assert reg(destination) == stack[0]
                if op == "call":
                    assert memory(reg(sp))[0] == decoded[1]["addr"], "Incorrect return address"
                if op == "ret":
                    assert int(gdb.parse_and_eval("$pc")) == stack[0]
            else:
                raise AssertionError("Instruction limit reached")
            if name in ("02", "04"):
                nop = next(s for s in states if s["instruction"] == "nop")
                a, b = ("rax", "rbx") if bits == 64 else ("eax", "ebx")
                assert (nop["registers"][a], nop["registers"][b]) == (100, 200)
                assert nop["stack"][:2] == [200, 100]
            if name == "01":
                assert any(s["registers"]["rcx"] == 200 and s["registers"]["rdx"] == 100 and s["delta"] == 0 for s in states)
            if name == "03":
                assert any(s["instruction"] == "nop" and s["registers"]["rax"] == 15 and s["delta"] == 0 for s in states)
            if name in ("05", "06"):
                a, b = ("rax", "rbx") if bits == 64 else ("eax", "ebx")
                expected = 0x1122334455667788 if bits == 64 else 0x11223344
                assert any(s["registers"][a] == expected and s["registers"][b] == 0x1234 and s["delta"] == 0 and s["step"] > 2 for s in states)
            lines.append("\nPASS: all stack transitions, pushed/popped values, return addresses, final stack/frame restoration, expected results, and exit status verified.\n")
            results[name] = {"bits": bits, "entry_sp": entry_sp, "entry_bp": entry_bp, "states": states, "exit_code": exit_codes[0]}
            destination = DOCS / name
            destination.mkdir(parents=True, exist_ok=True)
            # Strip terminal color codes while retaining the actual Pwndbg output.
            (destination / "pwndbg.txt").write_text(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", "".join(lines)))
            print("PASS " + name)
        finally:
            gdb.events.exited.disconnect(on_exit)
    (BUILD / (os.environ["STACK_EXAMPLE"] + ".json")).write_text(json.dumps(results, indent=2))


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    os.chdir(ROOT)
    for name, bits in BITS.items():
        subprocess.run(["nasm", "-f", f"elf{bits}", "-g", "-F", "dwarf", str(ROOT / f"07_stack/{name}.asm"), "-o", str(BUILD / (name + ".o"))], check=True)
        subprocess.run(["ld", "-m", "elf_x86_64" if bits == 64 else "elf_i386", str(BUILD / (name + ".o")), "-o", str(BUILD / name)], check=True)
        run = subprocess.run([str(BUILD / name)], capture_output=True, timeout=10)
        assert run.returncode == 0 and run.stdout == b"" and run.stderr == b"", (name, run)
        print(f"PASS native execution {name}: exit 0, empty stdout/stderr", flush=True)
    command = "python import runpy; runpy.run_path(" + repr(str(Path(__file__).resolve())) + ", run_name='__gdb__')"
    results = {}
    # Fresh GDB sessions also avoid stale architecture state between ELF64/ELF32.
    for name in BITS:
        subprocess.run(["gdb", "-q", "-batch", "-ex", command], check=True,
                       env={**os.environ, "STACK_EXAMPLE": name})
        results.update(json.loads((BUILD / (name + ".json")).read_text()))
    (BUILD / "results.json").write_text(json.dumps(results, indent=2))
    assert len(results) == 6


if __name__ == "__gdb__":
    trace()
elif __name__ == "__main__":
    main()
