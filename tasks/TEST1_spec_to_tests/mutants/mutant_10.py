"""Calculator engine with 15+ behaviors."""
"""MUTANT 10: Percent divides by 10 instead of 100"""
import threading
import re
import ast
import operator


class CalculatorError(Exception):
    """Calculator-specific error."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class Calculator:
    OVERFLOW_LIMIT = 2 ** 53

    def __init__(self):
        self._memory = 0.0
        self._history = []
        self._chain_value = None
        self._lock = threading.Lock()

    def _check_overflow(self, *values):
        for v in values:
            if isinstance(v, (int, float)) and abs(v) > self.OVERFLOW_LIMIT:
                raise CalculatorError("overflow")

    def _coerce(self, value):
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise CalculatorError("invalid_input")
        return float(value)

    def _record(self, op_str, result):
        self._history.append(f"{op_str} = {result}")
        if len(self._history) > 10:
            self._history = self._history[-10:]
        return result

    def _round(self, value):
        return round(value, 6)

    def add(self, a, b):
        with self._lock:
            a, b = self._coerce(a), self._coerce(b)
            self._check_overflow(a, b)
            result = self._round(a + b)
            self._check_overflow(result)
            return self._record(f"add({a}, {b})", result)

    def subtract(self, a, b):
        with self._lock:
            a, b = self._coerce(a), self._coerce(b)
            self._check_overflow(a, b)
            result = self._round(a - b)
            return self._record(f"subtract({a}, {b})", result)

    def multiply(self, a, b):
        with self._lock:
            a, b = self._coerce(a), self._coerce(b)
            self._check_overflow(a, b)
            result = self._round(a * b)
            self._check_overflow(result)
            return self._record(f"multiply({a}, {b})", result)

    def divide(self, a, b):
        with self._lock:
            a, b = self._coerce(a), self._coerce(b)
            self._check_overflow(a, b)
            if b == 0:
                raise CalculatorError("division_by_zero")
            result = self._round(a / b)
            return self._record(f"divide({a}, {b})", result)

    def sqrt(self, a):
        with self._lock:
            a = self._coerce(a)
            if a < 0:
                raise CalculatorError("domain_error")
            result = self._round(a ** 0.5)
            return self._record(f"sqrt({a})", result)

    def percent(self, base, pct):
        with self._lock:
            base, pct = self._coerce(base), self._coerce(pct)
            result = self._round(base * pct / 10)  # MUTANT: divides by 10 instead of 100
            return self._record(f"percent({base}, {pct})", result)

    def evaluate(self, expr):
        """Evaluate a math expression string with proper operator precedence."""
        with self._lock:
            try:
                tree = ast.parse(expr, mode='eval')
                result = self._round(self._eval_node(tree.body))
                self._check_overflow(result)
                return self._record(f"evaluate(\"{expr}\")", result)
            except (SyntaxError, TypeError):
                raise CalculatorError("invalid_input")

    def _eval_node(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
            }
            op_func = ops.get(type(node.op))
            if op_func is None:
                raise CalculatorError("invalid_input")
            if isinstance(node.op, ast.Div) and right == 0:
                raise CalculatorError("division_by_zero")
            return op_func(left, right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._eval_node(node.operand)
        else:
            raise CalculatorError("invalid_input")

    def chain(self, initial):
        """Start a chained operation."""
        return _Chain(self, self._coerce(initial))

    def memory_store(self, value):
        with self._lock:
            self._memory = self._coerce(value)

    def memory_recall(self):
        with self._lock:
            return self._memory

    def memory_clear(self):
        with self._lock:
            self._memory = 0.0

    def history(self):
        with self._lock:
            return list(self._history)

    def undo(self):
        with self._lock:
            if self._history:
                self._history.pop()

    def batch(self, operations):
        results = []
        for op in operations:
            name = op[0]
            args = op[1:]
            func = getattr(self, name, None)
            if func is None:
                raise CalculatorError("invalid_input")
            results.append(func(*args))
        return results

    def reset(self):
        with self._lock:
            self._memory = 0.0
            self._history = []
            self._chain_value = None


class _Chain:
    def __init__(self, calc, value):
        self._calc = calc
        self._value = value

    def add(self, n):
        self._value = self._calc._round(self._value + self._calc._coerce(n))
        return self

    def subtract(self, n):
        self._value = self._calc._round(self._value - self._calc._coerce(n))
        return self

    def multiply(self, n):
        self._value = self._calc._round(self._value * self._calc._coerce(n))
        return self

    def divide(self, n):
        n = self._calc._coerce(n)
        if n == 0:
            raise CalculatorError("division_by_zero")
        self._value = self._calc._round(self._value / n)
        return self

    def result(self):
        return self._value
