import sys
from antlr4 import *
from CustomLexer import CustomLexer
from PythonQLParser import PythonQLParser

def main(argv):
  inputStream = FileStream(sys.argv[1])
  lexer = CustomLexer(inputStream)
  stream = CommonTokenStream(lexer)
  parser = PythonQLParser(stream)
  tree = parser.file_input()
  print (tree.getPayload())

if __name__ == '__main__':
  main(sys.argv)
