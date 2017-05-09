import sys
import json, os
import termcolor as tc

def pinfo(m):
    print(tc.colored("* ", "cyan") + m, file=sys.stderr)

def perror(m):
    print(tc.colored("* ", "red") + m, file=sys.stderr)

buildData = json.load(open(os.path.join(os.path.dirname(__file__),"build.json")))
