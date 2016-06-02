import sys
import tempfile
from pythonql.Executor import *
from pythonql.parser.Preprocessor import makeProgramFromFile
import time

def runProgramFromFile(fname):
  before_time = time.time()
  program = makeProgramFromFile(fname)
  parse_time = time.time()
  exec(program)
  exec_time = time.time()
  return (parse_time-before_time, exec_time-parse_time)

def runProgramFromString(q):
  before_time = time.time()
  program = makeProgramFromString(q)
  parse_time = time.time()
  exec(program)
  exec_time = time.time()
  return (parse_time-before_time, exec_time-parse_time)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: RunPYQL <pythonql program>")
    sys.exit()

  (parse_time,exec_time) = runProgramFromFile(sys.argv[1])

  print("----Time: parsing=%.3f(s), execution=%.3f(s)" % (parse_time,
      exec_time))
