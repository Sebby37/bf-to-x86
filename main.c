#include <stdio.h>
#include <stdlib.h>
#include <string.h>

char* parse_token(char token) {
    static int num_loops = 0; // The number of loops so far
    static int loops[256];  // A stack of sorts to store the amount of loops
    static int current_loop = 0; // An index to the stack
    
    char* code = (char*) malloc(256);
    switch (token) {
        case '>': 
        {
            sprintf(code, "inc rsi\n");
            break;
        }
        case '<': 
        {
            sprintf(code, "dec rsi\n");
            break;
        }
        case '+': 
        {
            sprintf(code, "inc byte [rsi]\n");
            break;
        }
        case '-': 
        {
            sprintf(code, "dec byte [rsi]\n");
            break;
        }
        case '.': 
        {
            sprintf(code,   "mov rax, 1\n" // Write syscall
                            "mov rdi, 1\n" // File descriptor (stdout = 1)
                            "mov rdx, 1\n" // Num bytes to write (just one)
                            // No need to touch rsi, it's already got the current character's address in it
                            "syscall\n");
            break;
        }
        case ',': 
        {
            sprintf(code,   "mov rax, 0\n" // Read syscall
                            "mov rdi, 0\n" // File descriptor (stdin = 0)
                            "mov rdx, 1\n" // Num bytes to read (just one)
                            // No need to touch rsi, it's already got the current buffer address
                            "syscall\n");
            break;
        }
        case '[': 
        {
            num_loops++;
            loops[current_loop] = num_loops;
            current_loop ++;
            
            sprintf(code,   "loop_%d:\n"
                            "cmp byte [rsi], 0\n"
                            "je loop_end_%d\n", num_loops, num_loops);
            break;
        }
        case ']': 
        {
            if (current_loop <= 0 || num_loops <= 0) {
                perror("Error: Mismatched closing square bracket");
                return NULL;
            }
            
            current_loop --;
            sprintf(code,   "cmp byte [rsi], 0\n"
                            "jne loop_%d\n"
                            "loop_end_%d:\n", loops[current_loop], loops[current_loop]);
            break;
        }
        default:
        {
            sprintf(code, "; Why are we here?");
            break;
        }
    }
    
    return code;
}

int is_valid_token(char token) {
    // Yeah ok its not pretty but it works
    return  (token == '>') || (token == '<') || 
            (token == '+') || (token == '-') ||
            (token == '.') || (token == ',') ||
            (token == '[') || (token == ']');
}

int main(int argc, char** argv) {
    // Stoopid
    if (argc < 2) {
        perror("Error: No input file specified!\n");
        return 1;
    }
    if (argc < 3) {
        printf("Warning: No output file specified, using 'out.asm'\n");
    }
    
    // We like filenames
    char* in_filename = argv[1];
    char* out_filename = argc < 3 ? "out.asm" : argv[2];
    
    // Open please
    FILE* in_file = fopen(in_filename, "r");
    if (in_file == NULL) {
        perror("Failed to open input file\n");
        return 1;
    }
    
    // Also open output file pretty please
    FILE* out_file = fopen(out_filename, "w");
    if (out_file == NULL) {
        perror("Failed to open output file\n");
        return 1;
    }
    
    // Setup asm file
    fprintf(out_file,   "section .data\n"
                        "\ttape times 9999 db 0\n" // The brainfuck tape
                        "section .text\n"
                        "global _start\n"
                        "_start:\n"
                        "mov rsi, tape\n\n" // rsi = data_pointer
            );
    
    // Parsing time!
    char token;
    while ((token = fgetc(in_file)) != EOF) {
        // Make sure we have valid token
        if (!is_valid_token(token))
            continue;
        
        // Parse the token
        char* current_asm = parse_token(token);
        
        // Errored somewhere, we leave
        if (current_asm == NULL) {
            fclose(in_file);
            return 1;
        }
        
        // Print to file and freeeee!
        fprintf(out_file, "%s", current_asm);
        free(current_asm);
    }
    fclose(in_file);
    
    // Write the return asm and close
    fprintf(out_file,   "mov rax, 60\n" // Exit syscall
                        "xor rdi, rdi\n" // Return code 0 (funny way of setting rdi to 0)
                        "syscall"
            );
    fclose(out_file);
    
    return 0;
}