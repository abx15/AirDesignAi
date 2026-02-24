from __future__ import annotations

from typing import Any, Dict, List, Tuple

import sympy as sp


class MathSolverService:
    """Wrapper around SymPy to provide high-level solving utilities."""

    def __init__(self) -> None:
        self.x, self.y, self.z = sp.symbols("x y z")

    def _sympify(self, expression: str) -> sp.Expr:
        return sp.sympify(expression)

    def solve_generic(self, expression: str) -> Tuple[str, str]:
        """Attempt to solve a wide range of expressions.

        Returns a tuple of (solution_latex, steps_text).
        """
        try:
            # Handle potential simultaneous equations separated by semicolon or comma
            if ';' in expression or (',' in expression and '[' not in expression):
                parts = [p.strip() for p in expression.replace(';', ',').split(',')]
                eqs = [self._sympify(p) if '=' not in p else sp.Eq(self._sympify(p.split('=')[0]), self._sympify(p.split('=')[1])) for p in parts]
                # Determine variables
                vars_to_solve = list(set().union(*(eq.free_symbols for eq in eqs)))
                if not vars_to_solve:
                    vars_to_solve = [self.x]
                sol = sp.solve(eqs, vars_to_solve)
                return sp.latex(sol), f"Solved system of equations for {vars_to_solve}: {eqs} -> {sol}"

            expr = self._sympify(expression)

            # If the expression is an equation (contains Equality)
            if isinstance(expr, sp.Equality):
                # Solve for the first free symbol found, or x
                vars = list(expr.free_symbols)
                solve_for = vars[0] if vars else self.x
                sol = sp.solve(expr, solve_for)
                steps = f"Solved equation for {solve_for}: {sp.pretty(expr)} -> {sol}"
            else:
                # Try to interpret as 'expr = 0'
                eq = sp.Eq(expr, 0)
                vars = list(expr.free_symbols)
                solve_for = vars[0] if vars else self.x
                sol = sp.solve(eq, solve_for)
                steps = f"Solved expression {sp.pretty(expr)} = 0 for {solve_for} -> {sol}"

            solution_latex = sp.latex(sol)
            return solution_latex, steps
        except Exception as e:
            return f"Error: {str(e)}", f"Failed to solve: {expression}"

    def derivative(self, expression: str, var: str = "x") -> Tuple[str, str]:
        sym = sp.symbols(var)
        expr = self._sympify(expression)
        deriv = sp.diff(expr, sym)
        return sp.latex(deriv), f"Computed derivative d/d{var} of {sp.pretty(expr)}"

    def integral(self, expression: str, var: str = "x") -> Tuple[str, str]:
        sym = sp.symbols(var)
        expr = self._sympify(expression)
        integ = sp.integrate(expr, sym)
        return sp.latex(integ), f"Computed ∫ {sp.pretty(expr)} d{var}"

    def limit(self, expression: str, var: str, point: Any) -> Tuple[str, str]:
        sym = sp.symbols(var)
        expr = self._sympify(expression)
        lim = sp.limit(expr, sym, point)
        return sp.latex(lim), f"Computed limit of {sp.pretty(expr)} as {var} → {point}"

    def matrix_determinant(self, matrix_expr: List[List[str]]) -> Tuple[str, str]:
        mat = sp.Matrix([[self._sympify(e) for e in row] for row in matrix_expr])
        det = mat.det()
        return sp.latex(det), f"Computed determinant of matrix {mat}"

    def matrix_inverse(self, matrix_expr: List[List[str]]) -> Tuple[str, str]:
        mat = sp.Matrix([[self._sympify(e) for e in row] for row in matrix_expr])
        inv = mat.inv()
        return sp.latex(inv), f"Computed inverse of matrix {mat}"

    def factor_polynomial(self, expression: str) -> Tuple[str, str]:
        expr = self._sympify(expression)
        factored = sp.factor(expr)
        return sp.latex(factored), f"Factored polynomial {sp.pretty(expr)}"

    def trig_simplify(self, expression: str) -> Tuple[str, str]:
        expr = self._sympify(expression)
        simp = sp.simplify(expr)
        return sp.latex(simp), f"Simplified trigonometric expression {sp.pretty(expr)}"

    def build_graph_data(self, expression: str, var: str = "x") -> Dict[str, Any]:
        """Generate x/y pairs for plotting y = f(x)."""
        sym = sp.symbols(var)
        expr = self._sympify(expression)
        func = sp.lambdify(sym, expr, "numpy")

        import numpy as np

        xs = np.linspace(-10, 10, 400)
        ys = func(xs)

        return {
            "x": xs.tolist(),
            "y": [float(v) if sp.Float(v) else None for v in ys],
            "expression": expression,
        }


solver_service = MathSolverService()

