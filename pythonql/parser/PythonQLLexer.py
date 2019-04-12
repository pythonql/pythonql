import ply.lex as lex
import types
import re

# Token class, has all the necessary data for error reporting
# and reconstruction of the program

class PQLexerToken:
  def __init__(self, type, value, line_no, column):
    self.type = type
    self.value = value
    self.line_no = line_no
    self.column = column

  def __getitem__(self, index):
      return (self.type, self.value, self.line_no, self.column)[index]
  
  def __setitem__(self, index, value):
      if index == 0:
        self.type = value
      elif index == 1:
        self.value = value
      elif index == 2:
        self.line_no = value
      elif index == 3:
        self.column = value
    
  def __delitem__(self, index):
      if index == 0:
        self.type = None 
      elif index == 1:
        self.value = None
      elif index == 2:
        self.line_no = None 
      elif index == 3:
        self.column = None
        
  def __repr__(self):
    return "(%s,%s,%d,%d)" % (self.type, self.value, self.line_no, self.column)

# Monkey-patch method, we add it to the lexer object to
# be able to pushback a token back into the lexer

def pushback_token(self,token):
  self.pushback_queue.append(token)

# Monkey-patch method, we replace the lexer's token method with this method
# which returns pushed-back tokens, tracks opening and closing parens and
# constructs tokens with all the info we need

def get_token(self):
  output_token = None
  if not self.pushback_queue:
    output_token = self.old_token()
  else:
    output_token = self.pushback_queue.pop()
  if not output_token:
    return None
  if output_token.type in ['(', '[', '{']:
    self.opened += 1
  if output_token.type in [')', ']', '}']:
    self.opened -= 1
  output_token.value = PQLexerToken(output_token.type,
                                    output_token.value,
                                    self.lineno,
                                    self.lexpos - self.newlinepos)
  return output_token

# List of keywords 

keywords = [
    'DEF', 'RETURN', 'RAISE', 'FROM', 'IMPORT', 'AS',
    'GLOBAL', 'NONLOCAL', 'ASSERT', 'IF', 'ELIF',
    'ELSE', 'WHILE', 'FOR', 'LET', 'IN', 'TRY', 'FINALLY',
    'WITH', 'EXCEPT', 'LAMBDA', 'OR', 'AND', 'NOT', 'IS',
    'NONE', 'TRUE', 'FALSE', 'CLASS', 'YIELD', 'DEL',
    'PASS', 'CONTINUE', 'BREAK', 'SELECT', 'WHERE',
    'GROUP', 'BY', 'ORDER', 'WINDOW', 'PREVIOUS', 'FOLLOWING',
    'START', 'END', 'WHEN', 'AT', 'ONLY', 'TUMBLING', 'SLIDING',
    'ASC', 'DESC', 'COUNT', 'MATCH', 'EXACT', 'FILTER' ]

key_map = { k.lower():k for k in keywords if not k in ['NONE','TRUE','FALSE']}
key_map.update( {'None':'NONE', 'True':'TRUE', 'False':'FALSE'} )

# The lexer class
class Lexer:
  tokens = keywords + [

    # Literals, etc.
    'NEWLINE',
    'INDENT',
    'DEDENT',
    'STRING_LITERAL',
    'LONG_STRING_LITERAL',
    'NAME',
    'FLOAT_NUMBER',
    'DECIMAL_INTEGER',
    'OCT_INTEGER',
    'HEX_INTEGER',
    'BIN_INTEGER',
    'IMAG_NUMBER',

    # Multi-char operators
    'ELLIPSIS', 'POWER', 'LEFT_SHIFT', 'RIGHT_SHIFT', 'IDIV', 'EQUALS', 'GT_EQ',
    'LT_EQ', 'NOT_EQ_1', 'NOT_EQ_2', 'ARROW', 'ADD_ASSIGN', 'SUB_ASSIGN', 'MULT_ASSIGN',
    'AT_ASSIGN', 'DIV_ASSIGN', 'MOD_ASSIGN', 'AND_ASSIGN', 'OR_ASSIGN', 'XOR_ASSIGN',
    'LEFT_SHIFT_ASSIGN', 'RIGHT_SHIFT_ASSIGN', 'POWER_ASSIGN', 'IDIV_ASSIGN',
    'CHILD_AXIS', 'DESCENDENT_AXIS'
  ]

  # Rules for literals, etc

  # The rule for the newline is tricky, this is where
  # all the Python identation/deidentation is happening

  def t_NEWLINE(self,t):
    r'\n|\r'
    t.lexer.lineno += len(t.value)
    t.lexer.newlinepos = t.lexer.lexpos
    pos = t.lexer.lexpos
    data = t.lexer.lexdata

    # Consume all the whitespace until we hit something non-white or a newline
    while True:
      if pos >= len(data):
        return t
  
      if data[pos] in ['\n','\r'] or not re.match('\s',data[pos]):
        break

      pos += 1
    
    # If this is a line with just whitespace, or we're inside parenthesis,
    # don't return a token

    if data[pos] in ['\n', '\t', '#'] or t.lexer.opened > 0:
      return None

    ws = data[t.lexer.lexpos:pos]

    # Check if we went back to an older identation level, then
    # create some DEDENT tokens
    try:
      idx = t.lexer.indent_stack.index(ws)
      ndedents = len(t.lexer.indent_stack)-idx-1
      for i in range(ndedents):
        t.lexer.indent_stack.pop()
        dedent_tok = lex.LexToken()
        dedent_tok.type = 'DEDENT'
        dedent_tok.value = ''
        dedent_tok.lineno = t.lexer.lineno
        dedent_tok.lexpos = pos
        t.lexer.pushback_token(dedent_tok)

    # Otherwise, check if we have added an identation level and create
    # an IDENT token, or just return a newline

    except:
      last_ident = t.lexer.indent_stack[-1] if t.lexer.indent_stack else ""
      if ws.startswith(last_ident):
        indent_tok = lex.LexToken()
        indent_tok.type = 'INDENT'
        indent_tok.value = ws
        indent_tok.lineno = t.lexer.lineno
        indent_tok.lexpos = pos
        t.lexer.pushback_token(indent_tok)
        t.lexer.indent_stack.append(ws)

      # Current ident doesn't contain the previous ident, identation error!
      else:
        raise Exception("Bad ident at line %d" % t.lexer.lineno )
    return t

  # multi-qoute strings are pretty straightforward

  def t_LONG_STRING_LITERAL(self,t):
    r'([bB][rR]?|[uU]?[rR]?)("""|\'\'\')'
    pos = t.lexer.lexpos
    data = t.lexer.lexdata
    start_sym = data[t.lexer.lexpos-1]

    content_len = 0
    while True:
      if pos >= len(data):
        raise Exception("Unterminated string at line %d" % t.lexer.lineno)

      if data[pos] == start_sym:
        if content_len >= 2:
          if data[pos-1] == data[pos-2] == start_sym:
            break

      pos += 1
      content_len += 1

    pos += 1
    t.lexer.lexpos = pos
    t.value = data[t.lexpos:pos]
    return t

  # Some hairy business with backslash handling in single quote strings

  def t_STRING_LITERAL(self,t):
    r'([bB][rR]?|[uU]?[rR]?)("|\')'
    pos = t.lexer.lexpos
    data = t.lexer.lexdata
    start_sym = data[t.lexer.lexpos-1]
    prev_slash = False

    while True:
      if pos >= len(data) or data[pos] == '\n':
        raise Exception("Unterminated string at line %d" % t.lexer.lineno)

      if data[pos] == start_sym and not prev_slash:
        break

      if data[pos] == '\\':
        prev_slash = not prev_slash
      else: 
        prev_slash = False

      pos += 1

    pos += 1
    t.lexer.lexpos = pos
    t.value = data[t.lexpos:pos]
    return t

  # Keywords go here, as well as identifiers

  def t_NAME(self,t):
    r'[^\W0-9]\w*'
    if t.value in key_map:
      t.type = key_map[t.value]
    return t

  t_DECIMAL_INTEGER = r'([1-9][0-9]*|0+)'
  t_OCT_INTEGER = r'0[oO][0-7]+'
  t_HEX_INTEGER = r'0[xX][0-9a-fA-F]+'
  t_BIN_INTEGER = r'0[bB][01]+'

  t_IMAG_NUMBER = r'[0-9]*\.[0-9]+[eE][+-]?[0-9]+[jJ]|[0-9]+\.[eE][+-]?[0-9]+[jJ]|[0-9]+[eE][+-]?[0-9]+[jJ]|[0-9]*\.[0-9]+[jJ]|[0-9]+\.[jJ]|[0-9]+[jJ]'
  t_FLOAT_NUMBER = r'[0-9]*\.[0-9]+[eE][+-]?[0-9]+|[0-9]+\.[eE][+-]?[0-9]+|[0-9]+[eE][+-]?[0-9]+|[0-9]*\.[0-9]+|[0-9]+\.'

  t_ELLIPSIS = r'\.\.\.'
  t_POWER_ASSIGN = r'\*\*='
  t_POWER = r'\*\*'
  t_EQUALS = r'=='
  t_LEFT_SHIFT_ASSIGN = r'<<='
  t_LEFT_SHIFT = r'<<'
  t_RIGHT_SHIFT_ASSIGN = r'>>='
  t_RIGHT_SHIFT = r'>>'
  t_ADD_ASSIGN = r'\+='
  t_ARROW = r'->'
  t_SUB_ASSIGN = r'-='
  t_IDIV = r'//'
  t_LT_EQ = r'<='
  t_NOT_EQ_1 = r'<>'
  t_NOT_EQ_2 = r'!='
  t_GT_EQ = r'>='
  t_MULT_ASSIGN = r'\*='
  t_DIV_ASSIGN = r'/='
  t_AT_ASSIGN = r'@='
  t_MOD_ASSIGN = r'%='
  t_AND_ASSIGN = r'&='
  t_OR_ASSIGN = r'\|='
  t_XOR_ASSIGN = r'\^='
  t_IDIV_ASSIGN = r'//='
  t_CHILD_AXIS = r'\./'
  t_DESCENDENT_AXIS = r'\.//'
  
  literals = '.(),:;=[]|^&+-*/%~{}<>@'

  def t_comment(self,t):
    r'\#'
    pos = t.lexer.lexpos
    data = t.lexer.lexdata

    while True:
      if pos >= len(data) or data[pos] == '\n':
        break

      pos += 1

    t.lexer.lexpos = pos

  # When we hit EOF, we check whether we have "open" INDENTs left.
  # If that's the case, generate a DEDENT for every current INDENT

  def t_eof(self, t):
    if t.lexer.indent_stack != [""]:
      t.lexer.indent_stack.pop()
      dedent_tok = lex.LexToken()
      dedent_tok.type = 'DEDENT'
      dedent_tok.value = ''
      dedent_tok.lineno = t.lexer.lineno
      dedent_tok.lexpos = t.lexer.lexpos
      return dedent_tok
    return None
      
  t_ignore = ' \t'

  def t_error(self,t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

  def build(self,**kwargs):
    self.lexer = lex.lex(module=self, reflags=re.UNICODE, **kwargs)
    self.lexer.opened = 0
    self.lexer.newlinepos = 0
    self.lexer.indent_stack = [""]
    self.lexer.pushback_queue = []
 
    # WARNING: Monkey-patching :)

    self.lexer.pushback_token = types.MethodType(pushback_token,self.lexer)
    self.lexer.old_token = self.lexer.token
    self.lexer.token = types.MethodType(get_token,self.lexer)

  def test(self,str):
    self.lexer.input(str)
    while True:
      tok = self.lexer.token()
      if not tok:
        break
      print (tok)

if __name__=='__main__':
  import sys
  source_file = open(sys.argv[1])
  l = Lexer()
  l.build()
  str = "".join(source_file.readlines()) + "\n"
  print("Parsing:", repr(str))
  t = l.test(str)
  print(t) 
