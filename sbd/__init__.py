import sys
import termcolor as tc

def perror(m):
    print(tc.colored("* ", "red") + m, file=sys.stderr)
