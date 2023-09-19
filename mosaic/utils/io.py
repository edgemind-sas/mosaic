import sys

def update_console(text):
    num_lines = text.count("\n") + 1  # Count the number of lines

    # Move the cursor up by num_lines lines
    sys.stdout.write(f"\033[{num_lines}A")

    # Clear each line, move cursor down by one line, then move it back up.
    escape_sequences = ["\033[K\033[1B" for _ in range(num_lines - 1)] + ["\033[K"]
    sys.stdout.write(''.join(escape_sequences))

    # Move the cursor back up by num_lines lines
    sys.stdout.write(f"\033[{num_lines}A")

    # Print the new text
    sys.stdout.write(text)
    sys.stdout.flush()  # Flush the buffer to make sure it is displayed

