# 🧠 LauraSeFue Language - Lexer

Este proyecto implementa un **analizador léxico (Lexer)** para un lenguaje de programación personalizado llamado **LauraSeFue**.

El objetivo es transformar una cadena de texto (código fuente) en una secuencia de **tokens**, que luego serán utilizados por el parser para construir un AST.

---

## 🚀 ¿Qué es un Lexer?

Un **Lexer (analizador léxico)** es la primera fase de un compilador o intérprete.

Su función es:

- Leer el código fuente carácter por carácter
- Agruparlos en unidades llamadas **tokens**
- Clasificar cada token (operadores, palabras clave, identificadores, etc.)

Ejemplo:

```txt
input:  let x = 10 + 5
tokens: LET IDENTIFIER ASSIGN INTEGER PLUS INTEGER