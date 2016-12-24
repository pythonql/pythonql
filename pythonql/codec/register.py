import codecs, io, encodings
import sys
import traceback
from encodings import utf_8
from pythonql.parser.Preprocessor import makeProgramFromString

def pythonql_transform(stream):
    try:
        import_str = "\nfrom pythonql.Executor import *"
        prog_str = "".join(stream.readlines())
        if (prog_str):
          prog_str = import_str + prog_str
        else:
          return ''
        output = makeProgramFromString(prog_str)
    except Exception as ex:
        print(ex,file=sys.stderr)
        raise

    return output

def pythonql_transform_string(input):
    stream = io.StringIO(bytes(input).decode('utf-8'))
    return pythonql_transform(stream)

def pythonql_decode(input, errors='strict'):
    return pythonql_transform_string(input), len(input)

class PythonqlIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = b''
            return super(PythonqlIncrementalDecoder, self).decode(
                pythonql_transform_string(buff).encode('utf-8'), final=True)
        else:
            return ''

class PythonqlStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = io.StringIO(pythonql_transform(self.stream))

def search_function(encoding):
    if encoding != 'pythonql': return None
    # Assume utf8 encoding
    utf8=encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'pythonql',
        encode = utf8.encode,
        decode = pythonql_decode,
        incrementalencoder = utf8.incrementalencoder,
        incrementaldecoder = PythonqlIncrementalDecoder,
        streamreader = PythonqlStreamReader,
        streamwriter = utf8.streamwriter)

codecs.register(search_function)

