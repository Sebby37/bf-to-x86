build: main.c
	gcc main.c -o bf2x86
run: build
	./bf2x86 $(FILE)
	nasm -f elf64 -o out.o out.asm
	ld -o out -n -s out.o
	rm out.o
	./out
optimized:
	python3 main.py $(FILE)
	nasm -f elf64 -o out.o out.asm
	ld -o out -n -s out.o
	rm out.o
	./out
clean:
	rm bf2x86