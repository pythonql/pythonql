#!/bin/sh
antlr4 -o pythonql/parser -Dlanguage=Python3 -visitor PythonQL.g4
