from enum import IntEnum
from typing import (
    Callable,
    Dict,
    List,
    Optional
)
from laurasefue.tokens import Token, TokenType
from laurasefue.lexer import Lexer
from laurasefue import ast

class Precedences(IntEnum):
    LOWEST = 1
    OR=2
    AND=3
    EQUALS = 4       # ==
    LESSGREATER = 5  # > o <
    SUM = 6         # +
    PRODUCT = 7     # *
    PREFIX = 8      # -X o !X
    POWER=9
    CALL = 10

PRECEDENCES:Dict[TokenType,Precedences]={
    TokenType.OR: Precedences.OR,
    TokenType.AND: Precedences.AND,
    TokenType.EQ: Precedences.EQUALS,
    TokenType.DIF: Precedences.EQUALS,
    TokenType.LT: Precedences.LESSGREATER,
    TokenType.LTE: Precedences.LESSGREATER,
    TokenType.GT: Precedences.LESSGREATER,
    TokenType.GTE: Precedences.LESSGREATER,
    TokenType.PLUS: Precedences.SUM,
    TokenType.MINUS: Precedences.SUM,
    TokenType.MULTIPLY: Precedences.PRODUCT,
    TokenType.DIVISION: Precedences.PRODUCT,
    TokenType.MOD: Precedences.PRODUCT,
    TokenType.POW: Precedences.POWER,
    TokenType.LPAREN: Precedences.CALL
}        # myFunction(X)
PrefixParseFn=Callable[[],ast.Expression]
InfixParseFn=Callable[[ast.Expression],ast.Expression]

class Parser:

    def __init__(self, lexer:Lexer):
        self._lexer=lexer

        self._errors:List[str]=[]

        self._current_token:Optional[Token]=None
        self._peek_token:Optional[Token]=None

        self._prefix_parse_fns:Dict[TokenType,PrefixParseFn]={
            TokenType.IDENTIFIER: self._parse_identifier,
            TokenType.INTEGER: self._parse_integer_literal,
            TokenType.FLOAT: self._parse_float_literal,
            TokenType.STRING: self._parse_string_literal,
            TokenType.TRUE: self._parse_boolean_literal,
            TokenType.FALSE: self._parse_boolean_literal,
            TokenType.MINUS: self._parse_prefix_expression,
            TokenType.NEGATION: self._parse_prefix_expression,
            TokenType.LPAREN: self._parse_grouped_expression,
            TokenType.IF: self._parse_if_expression,
            TokenType.FUNCTION: self._parse_function_literal
        }

        self._infix_parse_fns:Dict[TokenType,InfixParseFn]={
            TokenType.PLUS: self._parse_infix_expression,
            TokenType.MINUS: self._parse_infix_expression,
            TokenType.MULTIPLY: self._parse_infix_expression,
            TokenType.DIVISION: self._parse_infix_expression,
            TokenType.MOD: self._parse_infix_expression,
            TokenType.POW: self._parse_infix_expression,
            TokenType.EQ: self._parse_infix_expression,
            TokenType.DIF: self._parse_infix_expression,
            TokenType.LT: self._parse_infix_expression,
            TokenType.LTE: self._parse_infix_expression,
            TokenType.GT: self._parse_infix_expression,
            TokenType.GTE: self._parse_infix_expression,
            TokenType.AND: self._parse_infix_expression,
            TokenType.OR: self._parse_infix_expression,
            TokenType.LPAREN: self._parse_call_expression
        }
        self._advance_tokens()
        self._advance_tokens()
    
    @property
    def errors(self)->List[str]:
        return self._errors
    
    def parse_program(self)->ast.Program:
        program=ast.Program()
        while self._current_token is not None or self._current_token.type != TokenType.EOF:
            statement=self._parse_statement()
            if statement is not None:
                program.statements.append(statement)
            self._advance_tokens()
            
        return program