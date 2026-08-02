import sys
import sympy as sp

sys.path.append('../AlgosSat')
from memo1a1.memo1a_algorithm import DpImpl


if __name__ == "__main__":
    k = sp.symbols("k", nonnegative=True, integer=True)
    p = sp.symbols("p", positive=True, integer=True)
    m = sp.symbols("m", nonnegative=True, integer=True)
    expr = sp.Sum(p * sp.binomial(p - 1, k - 1), (k, 1, m)) + 1

    print("General Form")
    simp_expr = sp.simplify(expr.doit())
    sp.print_latex(simp_expr)
    print()


    print("m = p Form")
    simp_expr = sp.simplify(expr.subs(m, p).doit())
    sp.print_latex(simp_expr)
    print()

    for it in range(1, 20):
        simp_expr = sp.expand(sp.simplify(expr.subs(m, sp.Integer(it)).doit()))
        print(f"Simplified for m = {it}")
        sp.print_latex(simp_expr)
        sp.print_latex(sp.O(simp_expr, (p, sp.oo)))
        print()

    print("f(p, m) = ?")
    dp_impl = DpImpl()
    for pi in range(1, 20):
        for mi in range(1, pi + 1):
            dp_impl(0, set([i+1 for i in range(pi)]), set([pi+1, pi+2]), {i: {j+1: 1 for j in range(pi+2)} for i in range(pi+1)}, mi)
            print(f"f({pi}, {mi}) = {sum(dp_impl.counter)} = {expr.subs([(p, pi), (m, mi)]).doit()}")