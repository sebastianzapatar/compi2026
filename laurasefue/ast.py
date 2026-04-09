from abc import ABC, abstractmethod
from typing import List, Optional

class Node(ABC):
    @abstractmethod
    def token_literal(self):
        pass
    @abstractmethod
    def __str__(self):
        pass
class Statement(Node):
    pass
class Expression(Node):
    pass
class Program(Node):
    def __init__(self):
        self.statements:List[Statement]=[]
    def token_literal(self):
        if self.statements:
            return self.statements[0].token_literal()
        return ''
class LetStament(Statement):
    """
    Nodo para declaracion de variables
    let <variable>=<valor>
    let resultado=8+5
    """
    def __init__(self,token, name:'identifier',value:Optional[Expression]):
        self.token=token
        self.name=name
        self.value=value
    def token_literal(self):
        return self.token.token_literal
    def __str__(self):
        value_str=str(self.value) if self.value else ''
        return f'let {self.name} = {value_str}'
    
class ReturnStament(Statement):
    """
    Ejemplo return x + 1
    """
    def __init__(self,token,return_value:Optional[Expression])->None:
        self.token=token
        self.return_value=return_value
        
        
class ExpressionStatement(Statement):
    """
    Nodo para una expresion usada como sentencia completa
    ejemplo mafenovinoalparcial(x)
    """
    def __init__(self,token,expression:Optional[Expression]=None):
        self.token=token
        self.expression=expression
    
    def token_literal(self):
        return self.token_literal
    def __str__(self):
        return str(self.expression) if self.expression else ''
    
        

