# This contains analysis of the assembly programs in contrast to EFLAGS (FLAGS SET)


## Preparations

The first thing to do was to ensure we compile the x32 programs that existed within the repository (we will compile the programs using the debug symbols for smooth debugging)

> Since the programs create object files, we will delete them as we are interested in the final output

```bash
$ pwd
/mnt/c/Users/manot/OneDrive/Documents/GitHub/assembly_programming_f/03_arithmetic

$ bash build.sh
[+] Compilation succeeded for ./add/add1.asm!
[*] Linking files: ./add/add1.o -> ./add/add1
...
[*] Linking files: ./sub/sub2.o -> ./sub/sub2
[+] Compilation succeeded for ./sub/sub3.asm!
[*] Linking files: ./sub/sub3.o -> ./sub/sub3
...
```


## Addition
01 - [Addition 1](./add/add1.md)

02 - [Addition 2](./add/add2.md)

03 - [Addition 3](./add/add3.md)


## Division
04 - [Division 1](./div/div1.md)

05 - [Division 2](./div/div2.md)

06 - [Division 3](./div/div3.md)

## Multiplication
07 - [Multiplication 1](./mul/mul1.md)

08 - [Multiplication 2](./mul/mul2.md)

09 - [Multiplication 3](./mul/mul3.md)

## Subtraction
10 - [Subtraction 1](./sub/sub1.md)

11 - [Subtraction 2](./sub/sub2.md)

12 - [Subtraction 3](./sub/sub3.md)

