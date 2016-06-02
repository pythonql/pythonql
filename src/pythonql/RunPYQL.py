import sys
import tempfile
from pythonql.Executor import *
from pythonql.parser.Preprocessor import makeProgram
import time

def runProgramFromFile(fname):
  before_time = time.time()
  program = makeProgram(fname)
  parse_time = time.time()
  exec(program)
  exec_time = time.time()
  return (parse_time-before_time, exec_time-parse_time)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: RunPYQL <pythonql program>")
    sys.exit()

  (parse_time,exec_time) = runProgramFromFile(fname)

  print("----Time: parsing=%.3f(s), execution=%.3f(s)" % (parse_time,
      exec_time))
