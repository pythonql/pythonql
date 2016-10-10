#!/bin/sh
antlr4 -o pythonql/parser -Dlanguage=Python3 -no-listener PythonQL.g4
