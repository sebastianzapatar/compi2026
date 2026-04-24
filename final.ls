print("=== Pruebas Finales del Intérprete ===");

print("");
print("--- 1. Aritmética y Flotantes ---");
let a = 10.5;
let b = 2;
print("10.5 * 2 =");
print(a * b);
print("10.5 / 2 =");
print(a / b);
print("2 ^ 3 + 1 =");
print(2 ^ 3 + 1);
print("17 % 5 =");
print(17 % 5);

print("");
print("--- 2. Cadenas de Texto (Strings) ---");
let saludo = "Hola";
let mundo = "Mundo";
print("Concatenación:");
print(saludo + " " + mundo + "!!!");
print("Igualdad de strings ('Laura' == 'Laura'):");
print("Laura" == "Laura");

print("");
print("--- 3. Condicionales (If / Elseif / Else) ---");
let verificar_numero = function(n) {
    if (n > 0) {
        return "Positivo";
    } elseif (n == 0) {
        return "Cero";
    } else {
        return "Negativo";
    }
};
print("El 5 es:");
print(verificar_numero(5));
print("El -3 es:");
print(verificar_numero(-3));
print("El 0 es:");
print(verificar_numero(0));

print("");
print("--- 4. Bucle While con Continue y Break ---");
let i = 0;
let pares = 0;
while (i < 10) {
    let i = i + 1;
    if (i % 2 != 0) {
        continue;
    }
    if (i > 8) {
        break;
    }
    let pares = pares + i;
}
print("Suma de pares <= 8 usando while (2+4+6+8 = 20):");
print(pares);

print("");
print("--- 5. Bucle For ---");
let sum_for = 0;
for (let j = 1; j <= 5; let j = j + 1) {
    let sum_for = sum_for + j;
}
print("Suma 1 a 5 usando for (15):");
print(sum_for);

print("");
print("--- 6. Funciones y Closures ---");
let crear_multiplicador = function(factor) {
    return function(x) { return x * factor; };
};
let triple = crear_multiplicador(3);
print("Closure triple(7) =");
print(triple(7));

print("");
print("--- 7. Funciones Recursivas ---");
let fact = function(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
};
print("Factorial(5) =");
print(fact(5));

let fib = function(n) {
    if (n <= 1) { return n; }
    return fib(n - 1) + fib(n - 2);
};
print("Fibonacci(7) =");
print(fib(7));

print("");
print("--- 8. Evaluación Lógica Extrema ---");
print("Probando !!!!!!!!!!!!!false (13 bangs)");
let muchos_bangs = !!!!!!!!!!!!!false;
print(muchos_bangs);
