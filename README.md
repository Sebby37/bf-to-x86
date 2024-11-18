# Brainfuck to x86_64 Compiler!
A little project I made today to learn a bit of x86 asm, as well as brush up on some C. It compiles brainfuck to (not particularly efficient) x86_64 assembly. If I decide to work on this more I'll probably try to make it more efficient by grouping tokens, using methods for the print/read tokens.

Oh yeah, it should be [nice-compliant](https://www.muppetlabs.com/~breadbox/bf/standards.html) I think. I'm currently storing each value on the tape as a byte too.

To run it, simply run `make` and then run `./bf2x86 [Input File] [Output File (optional, defaults to out.asm)]`!

Now this project doesn't have an assembler/linker or anything, so to make testing a bit easier I added the the `run` option to the Makefile, simply pass in a brainfuck source file as `FILE=your_file.b` into the make command (example: `make run FILE=do_the_thing.b`) and it'll call compile, assemble (using nasm), link (using ld) and execute it!

Note that I wrote this project entirely on Linux (Mint btw), so you'll probably need a linux machine or wsl to run this, idk if Windows comes with ld or if nasm has builds for Windows.