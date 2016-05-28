import sys
import tempfile
from pythonql.Executor import *
from pythonql.parser.Preprocessor import makeProgram
import subprocess

if len(sys.argv) != 2:
  print("Usage: RunPYQL <pythonql program>")
  sys.exit()

program = makeProgram( sys.argv[1] )
exec(program)
