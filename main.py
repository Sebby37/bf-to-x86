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
    # Pretty please valid input
    if len(sys.argv) < 2:
        print("Error: No input file specified!")
        return
    if len(sys.argv) < 3:
        print("Warning: No output file specified, defaulting to 'out.asm'")
    
    # Keeping track of arithmetics
    last_arithmetics = {
        "+": 0,
        "-": 0,
        ">": 0,
        "<": 0
    }
    
    # Keeping track of IO
    print_calls = 0
    read_calls = 0
    
    # Keeping track of loops
    loop_stack = []
    num_loops = 0
    
    # The beginning of the asm
    output = [
        # Allocate the space for the tape (but not really, by putting it in .bss its not stored in the executable and we get teensy ones)
        "section .bss",
        "tape resb 9999",
        
        "section .text",
        "global _start",
        "_start:",
        "mov rsi,tape",
        
        # Setting rdx to 1 (uses less bytes than `mov rdx,1`)
        # We can do this at the very start, as rdx never changes in our program and is in fact used for the syscalls
        # By keeping rdx at 1, we can mov it to the registers when needed for syscalls, saving precious instruction space
        "xor rdx,rdx",
        "inc rdx",
        ""
    ]
    
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
                # When we have more than 1 grouped arithmetic instructions, we can directly place the amount into the instruction
                match inst.operation:
                    case Operations.INC:
                        output.append(f"add byte [rsi],{inst.num}")
                    case Operations.DEC:
                        output.append(f"sub byte [rsi],{inst.num}")
                    case Operations.PTR_INC:
                        output.append(f"add rsi,{inst.num}")
                    case Operations.PTR_DEC:
                        output.append(f"sub rsi,{inst.num}")
            else:
                # When we only have 1 arithmetic inst, we can just use inc and dec as it uses less instruction space
                match inst.operation:
                    case Operations.INC:
                        output.append(f"inc byte [rsi]")
                    case Operations.DEC:
                        output.append(f"dec byte [rsi]")
                    case Operations.PTR_INC:
                        output.append(f"inc rsi")
                    case Operations.PTR_DEC:
                        output.append(f"dec rsi")
                        
        elif inst.type == InstTypes.IO:
            match inst.operation:
                case Operations.PRINT:
                    if print_calls > 4:
                        output.append("call print")
                    else:
                        output.extend([
                            # Sets rax and rdi to 1, as rdx is always 1 and we use less instruction space
                            "",
                            "mov rax,rdx",
                            "mov rdi,rdx",
                            "syscall",
                            ""
                        ])
                case Operations.READ:
                    if read_calls > 4:
                        output.append("call read")
                    else:
                        output.extend([
                            # Sets rax and rdx to 0 using even less instruction space
                            "",
                            "xor rax,rax",
                            "xor rdi,rdi",
                            "syscall",
                            ""
                        ])
                        
        elif inst.type == InstTypes.LOOP:
            match inst.operation:
                case Operations.LOOP_START:
                    output.extend([
                         "",
                        f"loop_{inst.num}:",
                         "cmp byte [rsi],0",
                        f"je loop_end_{inst.num}",
                         ""
                    ])
                case Operations.LOOP_END:
                    output.extend([
                         "",
                         "cmp byte [rsi],0",
                        f"jne loop_{inst.num}",
                        f"loop_end_{inst.num}:",
                         ""
                    ])
    
    # Finish off - Add exit statement
    output.extend([
        "",
        "mov rax,60",  # Syscall code 60 for exit
        "xor rdi,rdi", # Return code 0
        "syscall"      # Do the thing
    ])
    
    # And add the IO functions if needed
    if print_calls > 4:
        output.extend([
            "",
            "print:",
                "mov rax,rdx",
                "mov rdi,rdx",
                "syscall",
                "ret"
        ])
    if read_calls > 4:
        output.extend([
            "",
            "read:",
                "xor rax,rax",
                "xor rdi,rdi",
                "syscall",
                "ret"
        ])
    
    # And finally, write it to the output file
    open("out.asm" if len(sys.argv) < 3 else sys.argv[2], "w+").write("\n".join(output))

if __name__ == "__main__":
    main()