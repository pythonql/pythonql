# Generated from java-escape by ANTLR 4.5
from antlr4 import *

# This class defines a complete generic visitor for a parse tree produced by PythonQLParser.

class PythonQLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by PythonQLParser#single_input.
    def visitSingle_input(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#file_input.
    def visitFile_input(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#eval_input.
    def visitEval_input(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#decorator.
    def visitDecorator(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#decorators.
    def visitDecorators(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#decorated.
    def visitDecorated(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#funcdef.
    def visitFuncdef(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#parameters.
    def visitParameters(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#typedargslist.
    def visitTypedargslist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#tfpdef.
    def visitTfpdef(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#varargslist.
    def visitVarargslist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#vfpdef.
    def visitVfpdef(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#stmt.
    def visitStmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#simple_stmt.
    def visitSimple_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#small_stmt.
    def visitSmall_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#expr_stmt.
    def visitExpr_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#testlist_star_expr.
    def visitTestlist_star_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#augassign.
    def visitAugassign(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#del_stmt.
    def visitDel_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#pass_stmt.
    def visitPass_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#flow_stmt.
    def visitFlow_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#break_stmt.
    def visitBreak_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#continue_stmt.
    def visitContinue_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#return_stmt.
    def visitReturn_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#yield_stmt.
    def visitYield_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#raise_stmt.
    def visitRaise_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#import_stmt.
    def visitImport_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#import_name.
    def visitImport_name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#import_from.
    def visitImport_from(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#import_as_name.
    def visitImport_as_name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#dotted_as_name.
    def visitDotted_as_name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#import_as_names.
    def visitImport_as_names(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#dotted_as_names.
    def visitDotted_as_names(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#dotted_name.
    def visitDotted_name(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#global_stmt.
    def visitGlobal_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#nonlocal_stmt.
    def visitNonlocal_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#assert_stmt.
    def visitAssert_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#compound_stmt.
    def visitCompound_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#if_stmt.
    def visitIf_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#while_stmt.
    def visitWhile_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#for_stmt.
    def visitFor_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#try_stmt.
    def visitTry_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#with_stmt.
    def visitWith_stmt(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#with_item.
    def visitWith_item(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#except_clause.
    def visitExcept_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#suite.
    def visitSuite(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#test.
    def visitTest(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#path_step.
    def visitPath_step(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#child_path_step.
    def visitChild_path_step(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#desc_path_step.
    def visitDesc_path_step(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#pred_path_step.
    def visitPred_path_step(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#old_test.
    def visitOld_test(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#test_nocond.
    def visitTest_nocond(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#lambdef.
    def visitLambdef(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#lambdef_nocond.
    def visitLambdef_nocond(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#or_test.
    def visitOr_test(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#and_test.
    def visitAnd_test(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#not_test.
    def visitNot_test(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#comparison.
    def visitComparison(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#comp_op.
    def visitComp_op(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#star_expr.
    def visitStar_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#expr.
    def visitExpr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#xor_expr.
    def visitXor_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#and_expr.
    def visitAnd_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#shift_expr.
    def visitShift_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#arith_expr.
    def visitArith_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#term.
    def visitTerm(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#factor.
    def visitFactor(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#power.
    def visitPower(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#atom.
    def visitAtom(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#query_expression.
    def visitQuery_expression(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#select_clause.
    def visitSelect_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#selectvar.
    def visitSelectvar(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#for_clause.
    def visitFor_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#for_clause_entry.
    def visitFor_clause_entry(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#let_clause.
    def visitLet_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#let_clause_entry.
    def visitLet_clause_entry(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#window_clause.
    def visitWindow_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#tumbling_window.
    def visitTumbling_window(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#sliding_window.
    def visitSliding_window(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#window_start_cond.
    def visitWindow_start_cond(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#window_end_cond.
    def visitWindow_end_cond(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#opt_only.
    def visitOpt_only(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#window_vars.
    def visitWindow_vars(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#current_item.
    def visitCurrent_item(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#positional_var.
    def visitPositional_var(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#previous_var.
    def visitPrevious_var(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#next_var.
    def visitNext_var(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#order_by_clause.
    def visitOrder_by_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#orderlist.
    def visitOrderlist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#orderlist_el.
    def visitOrderlist_el(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#group_by_clause.
    def visitGroup_by_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#group_by_vars.
    def visitGroup_by_vars(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#group_by_var.
    def visitGroup_by_var(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#where_clause.
    def visitWhere_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#count_clause.
    def visitCount_clause(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#testlist_comp.
    def visitTestlist_comp(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#trailer.
    def visitTrailer(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#subscriptlist.
    def visitSubscriptlist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#subscript.
    def visitSubscript(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#sliceop.
    def visitSliceop(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#exprlist.
    def visitExprlist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#testlist.
    def visitTestlist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#dictorsetmaker.
    def visitDictorsetmaker(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#classdef.
    def visitClassdef(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#arglist.
    def visitArglist(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#argument.
    def visitArgument(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#comp_iter.
    def visitComp_iter(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#comp_for.
    def visitComp_for(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#comp_if.
    def visitComp_if(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#yield_expr.
    def visitYield_expr(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#yield_arg.
    def visitYield_arg(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#string.
    def visitString(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#number.
    def visitNumber(self, ctx):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by PythonQLParser#integer.
    def visitInteger(self, ctx):
        return self.visitChildren(ctx)


