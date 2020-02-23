# Base class for all operators
class operator:
 
  # Return a set of variables, defined by this operator
  def defined_vars(self):
    return set()

class OpTreeNode:
  def __init__(self,op,left_child=None,right_child=None):
    self.op = op
    self.left_child = left_child
    self.right_child = right_child
    self.parent = None

  # Convert a linear plan (with no joins) to a list of nodes
  def as_list(self):
    if self.right_child:
      raise "Converting a tree to a list"

    return [self] + (self.left_child.as_list() if self.left_child else [])

  # Convert a linear plan (with no joins) to a reversed list of nodes
  def as_list_reversed(self):
    res = self.as_list()
    res.reverse()
    return res

  # Iterate over all children via inorder traversal
  def visit(self):
    yield self
    if self.left_child:
        for x in self.left_child.visit():
            yield x
    if self.right_child:
        for x in self.right_child.visit():
            yield x

  # Compute the set of variables, defined in this subplan
  def defined_vars(self):
    vars = set()

    if self.left_child:
      vars = self.left_child.defined_vars()

    if self.right_child:
      vars = vars.union( self.right_child.defined_vars() )

    return vars.union( self.op.defined_vars() )

  # Compute a set of variables that are used above this operator
  def used_vars_above(self):
    vars = set()

    node = self.parent
    while node:
        vars = vars.union( node.op.used_vars() )
        node = node.parent

    return vars

  # Compute all the parents in the plan
  def compute_parents(self):
    if self.left_child:
        self.left_child.parent = self
        self.left_child.compute_parents()
    if self.right_child:
        self.right_child.parent = self
        self.right_child.compute_parents()

  # Replace this subplan with another one:
  def replace(self,other):
    self.op = other.op
    self.left_child = other.left_child
    self.right_child = other.right_child

  # Execute this subtree
  def execute(self, table, prior_lcs, prior_globs):
    if self.right_child:
        return self.op.execute(table,
                               prior_lcs,
                               prior_globs,
                               self.left_child,
                               self.right_child)
    else:
        if self.left_child:
            table = self.left_child.execute(table, prior_lcs, prior_globs)
        return self.op.execute(table, prior_lcs, prior_globs)


  # return a string representation of the plan
  def __repr__(self):
    return self.string_repr(0)

  # return a string representation of the plan
  def string_repr(self,nTabs):
    res = "   " * nTabs
    res += repr(self.op)
    if self.right_child:
      res += "\n"
      if self.left_child:
          res += self.left_child.string_repr(nTabs+1)
      else:
          res += "   " * (nTabs+1) + "None"
      res += "\n"
      res += self.right_child.string_repr(nTabs+1)

    elif self.left_child:
      res += "\n"
      res += self.left_child.string_repr(nTabs+1)

    return res

def plan_from_list(l):
  l2 = list(l)
  l2.reverse()
  res = None
  for x in l2:
    res = OpTreeNode(x,res)

  return res

