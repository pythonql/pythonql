#!/Users/pavel/.pyenv/shims/python3

import sys
import tempfile
from pythonql.Executor import *
from pythonql.parser.Preprocessor import makeProgramFromFile
from pythonql.parser.Preprocessor import makeProgramFromString
import time

def runProgramFromFile(fname):
  start_time = time.time()
  program = makeProgramFromFile(fname)
  print(program)
  before_exec = time.time()
  exec(program,globals(),locals())
  exec_time = time.time()
  return (before_exec-start_time,exec_time-before_exec)

def runProgramFromString(q):
  start_time = time.time()
  program = makeProgramFromString(q)
  before_exec = time.time()
  exec(program)
  exec_time = time.time()
  return (before_exec-start_time,exec_time-before_exec)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: RunPYQL <pythonql program>")
    sys.exit()

  (parse_time,exec_time) = runProgramFromFile(sys.argv[1])

  print("----Time: parsing=%.3f(s), execution=%.3f(s)" % (parse_time,
      exec_time))
