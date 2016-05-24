import sys
import tempfile
from Executor import *
from parser.Preprocessor import makeProgram
import subprocess

if len(sys.argv) != 2:
  print("Usage: RunPYQL <pythonql program>")
  sys.exit()

program = makeProgram( sys.argv[1] )
exec(program)
