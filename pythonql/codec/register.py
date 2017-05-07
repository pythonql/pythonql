import codecs, cStringIO, encodings
import sys
import traceback
from encodings import utf_8
from pythonql.parser.Preprocessor import makeProgramFromString

def pythonql_transform(stream):
    try:
        import_str = "from pythonql.Executor import *"
        prog_str = "".join(stream.readlines())
        if (prog_str):
          prog_str = import_str + prog_str
        output = makeProgramFromString(prog_str)
    except Exception as ex:
        sys.stderr.write(ex.message + '\n')
        raise

    return output

def pythonql_transform_string(input):
    stream = cStringIO.StringIO(input)
    return pythonql_transform(stream)

def pythonql_decode(input, errors='strict'):
    return ut8.decode(pythonql_transform_string(input), errors)

class PythonqlIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            return super(PythonqlIncrementalDecoder, self).decode(
                pythonql_transform_string(buff), final=True)

class PythonqlStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = cStringIO.StringIO(pythonql_transform(self.stream))

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

