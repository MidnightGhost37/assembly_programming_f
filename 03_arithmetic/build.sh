#!/usr/bin/env bash
for assmname in $(find . -name "*.asm" -not -empty 2>/dev/null); do
    FILENAME="${assmname%.asm}"
    OBJECTFILE="$FILENAME.o"
    if nasm -f elf32 -g -F dwarf "$assmname" -o "$OBJECTFILE"; then
        echo "[+] Compilation succeeded for $assmname!"
        echo "[*] Linking files: $OBJECTFILE -> $FILENAME"
        ld -m elf_i386 "$OBJECTFILE" -o "$FILENAME"

        echo "[*] Cleaning up: removing $OBJECTFILE"
        rm "$OBJECTFILE"
    else
        echo "[-] Compilation failed for $assmname!"
    fi
done
