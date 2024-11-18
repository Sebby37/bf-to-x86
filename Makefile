build: main.c
	gcc main.c -o bf2x86
run: build
	./bf2x86 $(FILE)
	nasm -f elf64 -o out.o out.asm
	ld -o out out.o
	rm out.o
	rm out.asm
	./out
clean:
	rm bf2x86