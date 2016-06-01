import sys
import tempfile
from pythonql.Executor import *
from pythonql.parser.Preprocessor import makeProgram
import time

if len(sys.argv) != 2:
  print("Usage: RunPYQL <pythonql program>")
  sys.exit()

before_time = time.time()
program = makeProgram( sys.argv[1] )
parse_time = time.time()
exec(program)
exec_time = time.time()

print("----Time: parsing=%.3f(s), execution=%.3f(s)" % (parse_time-before_time,
      exec_time-parse_time))
