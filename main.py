import sys
from enum import Enum
from dataclasses import dataclass

@dataclass
class Instruction:
    type: int       # The type (arithmetic, IO, loop)
    operation: int  # The operation to be performed (increment/decrement (that with ptr), I/O, begin/end loop)
    num: int        # The consecutive number of these for arithmetic, or the number of them that exist for IO (not really used), or the loop num

class InstTypes(Enum):
    ARITHMETIC = 0
    IO = 1
    LOOP = 2

class Operations(Enum):
    INC = 0         # Increment memory value
    DEC = 1         # Decrement memory value
    PTR_INC = 2     # Increment pointer
    PTR_DEC = 3     # Decrement pointer
    PRINT = 4       # Print current character
    READ = 5        # Read current character from STDIN
    LOOP_START = 6  # Begin loop, jump to end if value at ptr == 0
    LOOP_END = 7    # End loop, jump to beginning if value at ptr != 0
    
def token_to_op(token: str):
    return {
        "+": Operations.INC,
        "-": Operations.DEC,
        ">": Operations.PTR_INC,
        "<": Operations.PTR_DEC,
        ".": Operations.PRINT,
        ",": Operations.READ,
        "[": Operations.LOOP_START,
        "]": Operations.LOOP_END
    }[token]

def main():
    if len(sys.argv) < 2:
        print("Error: No input file specified!")
        return
    if len(sys.argv) < 3:
        print("Warning: No output file specified, defaulting to 'out.asm'")
    
    last_arithmetics = {
        "+": 0,
        "-": 0,
        ">": 0,
        "<": 0
    }
    
    print_calls = 0
    read_calls = 0
    
    loop_stack = []
    num_loops = 0
    
    output = "section .bss\n" + "tape resb 9999\n" + "section .text\n" + "global _start\n" + "_start:\n" + "mov rsi,tape\n" + "xor rdx,rdx\n" + "inc rdx\n\n"
    
    instruction_list: list[Instruction] = []
    
    # Parse tokens to instruction list
    with open(sys.argv[1]) as in_file:
        last_token = None
        for token in in_file.read():
            # Make sure token is valid
            if token not in ("+", "-", "<", ">", ".", ",", "[", "]"):
                continue
            
            # Check for duplicate arithmetic tokens so we can group them
            if last_token == token and token in last_arithmetics.keys():
                last_arithmetics[token] += 1
            # No more duplicates
            if last_token != token and last_token in last_arithmetics.keys():
                instruction_list.append(Instruction(InstTypes.ARITHMETIC, token_to_op(last_token), last_arithmetics[last_token] + 1))
                last_arithmetics[last_token] = 0
                
            # Check for IO tokens
            if token == ".":
                print_calls += 1
                instruction_list.append(Instruction(InstTypes.IO, Operations.PRINT, print_calls))
            if token == ",":
                read_calls += 1
                instruction_list.append(Instruction(InstTypes.IO, Operations.READ, read_calls))
            
            # Check for loop tokens
            if token == "[":
                num_loops += 1
                loop_stack.append(num_loops)
                instruction_list.append(Instruction(InstTypes.LOOP, Operations.LOOP_START, loop_stack[-1]))
            if token == "]":
                instruction_list.append(Instruction(InstTypes.LOOP, Operations.LOOP_END, loop_stack.pop()))
            
            last_token = token
            
    # Convert instructions to assembly
    for inst in instruction_list:
        if inst.type == InstTypes.ARITHMETIC:
            if inst.num > 1:
                match inst.operation:
                    case Operations.INC:
                        output += f"add byte [rsi],{inst.num}\n\n"
                    case Operations.DEC:
                        output += f"sub byte [rsi],{inst.num}\n\n"
                    case Operations.PTR_INC:
                        output += f"add rsi,{inst.num}\n\n"
                    case Operations.PTR_DEC:
                        output += f"sub rsi,{inst.num}\n\n"
            else:
                match inst.operation:
                    case Operations.INC:
                        output += f"inc byte [rsi]\n\n"
                    case Operations.DEC:
                        output += f"dec byte [rsi]\n\n"
                    case Operations.PTR_INC:
                        output += f"inc rsi\n\n"
                    case Operations.PTR_DEC:
                        output += f"dec rsi\n\n"
        elif inst.type == InstTypes.IO:
            match inst.operation:
                case Operations.PRINT:
                    if print_calls > 4:
                        output += "call print\n\n"
                    else:
                        output += "mov rax,rdx\n" + "mov rdi,rdx\n" + "syscall\n\n"
                case Operations.READ:
                    if read_calls > 4:
                        output += "call read\n\n"
                    else:
                        output += "xor rax,rax\n" + "xor rdi,rdi\n" + "syscall\n\n"
        elif inst.type == InstTypes.LOOP:
            match inst.operation:
                case Operations.LOOP_START:
                    output += f"loop_{inst.num}:\n" + "cmp byte [rsi],0\n" + f"je loop_end_{inst.num}\n\n"
                case Operations.LOOP_END:
                    output += "cmp byte [rsi],0\n" + f"jne loop_{inst.num}\n" + f"loop_end_{inst.num}:\n\n"
    
    # Finish off - Add exit statement
    output += "mov rax,60\n" + "xor rdi,rdi\n" + "syscall\n\n"
    
    # And add the IO functions if needed
    if print_calls > 4:
        output += "print:\n" + "mov rax,rdx\n" + "mov rdi,rdx\n" + "syscall\n" + "ret\n\n"
    if read_calls > 4:
        output += "read:\n"  + "xor rax,rax\n" + "xor rdi,rdi\n" + "syscall\n" + "ret\n\n"
    
    # And finally, write it to the output file
    open("out.asm" if len(sys.argv) < 3 else sys.argv[2], "w+").write(output)

if __name__ == "__main__":
    main()