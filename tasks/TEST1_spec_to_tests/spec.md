# TEST1: Write Tests from Specification

## Goal
Write comprehensive tests for the calculator engine that catch bugs through mutation testing.

## Calculator Specification — 15 Behaviors

### Basic Arithmetic
1. `calc.add(a, b)` returns `a + b`
2. `calc.subtract(a, b)` returns `a - b`
3. `calc.multiply(a, b)` returns `a * b`
4. `calc.divide(a, b)` returns `a / b`

### Error Handling
5. `calc.divide(a, 0)` raises `CalculatorError("division_by_zero")`
6. Numbers > 2^53 raise `CalculatorError("overflow")`
7. `calc.sqrt(-1)` raises `CalculatorError("domain_error")`

### Chained Operations
8. `calc.chain(5).add(3).multiply(2).result()` returns `16.0`
   - Chain starts with initial value, applies operations sequentially

### Memory
9. `calc.memory_store(42)` stores value; `calc.memory_recall()` returns `42.0`
10. `calc.memory_clear()` clears memory; subsequent `memory_recall()` returns `0.0`

### Precision
11. Results are rounded to 6 decimal places
    - `calc.divide(1, 3)` returns `0.333333` (not `0.3333333...`)

### Percentage
12. `calc.percent(200, 15)` returns `30.0` (15% of 200)

### Expression Parsing
13. `calc.evaluate("2 + 3 * 4")` returns `14.0` (follows order of operations)
    - Supports: +, -, *, /, parentheses
    - `calc.evaluate("(2 + 3) * 4")` returns `20.0`

### History
14. `calc.history()` returns list of last 10 operations as strings
    - Format: `"add(1, 2) = 3.0"`
    - Only keeps last 10

### Undo
15. After `calc.add(1, 2)` then `calc.undo()`, the last operation is reversed
    - History entry is also removed

### Batch Mode
16. `calc.batch([("add", 1, 2), ("multiply", 3, 4)])` returns `[3.0, 12.0]`

### Reset
17. `calc.reset()` clears history, memory, and chain state

### Type Coercion
18. String numeric inputs auto-convert: `calc.add("5", "3")` returns `8.0`
19. Non-numeric strings raise `CalculatorError("invalid_input")`

### Thread Safety
20. Concurrent operations from 10 threads must not corrupt state

## Test Cases Table

| # | Operation | Expected | Notes |
|---|-----------|----------|-------|
| 1 | add(1, 2) | 3.0 | Basic |
| 2 | divide(10, 0) | CalculatorError("division_by_zero") | Error |
| 3 | add(2**53 + 1, 1) | CalculatorError("overflow") | Boundary |
| 4 | sqrt(-4) | CalculatorError("domain_error") | Domain |
| 5 | chain(10).add(5).multiply(2).result() | 30.0 | Chaining |
| 6 | memory_store(99); memory_recall() | 99.0 | Memory |
| 7 | divide(1, 3) | 0.333333 | Precision |
| 8 | percent(200, 15) | 30.0 | Percentage |
| 9 | evaluate("2 + 3 * 4") | 14.0 | Precedence |
| 10 | evaluate("(2 + 3) * 4") | 20.0 | Parentheses |
| 11 | 11 operations; history() length | 10 | History cap |
| 12 | add(1,2); undo(); history() | [] | Undo |
| 13 | batch([("add",1,2),("multiply",3,4)]) | [3.0, 12.0] | Batch |
| 14 | reset(); memory_recall() | 0.0 | Reset |
| 15 | add("5", "3") | 8.0 | Coercion |
| 16 | add("abc", 1) | CalculatorError("invalid_input") | Bad input |
| 17 | subtract(10, 3) | 7.0 | Basic |
| 18 | multiply(0, 100) | 0.0 | Zero |
| 19 | divide(7, 2) | 3.5 | Float |
| 20 | 10 threads each calling add(1,1) | No exceptions | Thread safety |

## Grading
- Phase 1: All tests must pass on correct engine (pytest passes, branch coverage > 80%)
- Phase 2: Tests must catch at least 7/10 mutant engines (each has one subtle bug)

## Deliverables
- `calculator/test_engine.py` with at least 15 test functions
- Verifier must run tests and verify coverage + mutation detection
