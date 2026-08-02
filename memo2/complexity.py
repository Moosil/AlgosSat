import math

from sympy import oo, Rational
import sympy as sp
from sympy.abc import k


class Complexity:
    @classmethod
    def _return(cls):
        return 1

    @classmethod
    def _while(cls, f, n):
        return n * (1 + f(n)) + 1

    @classmethod
    def _for(cls, n):
        return 1 + n

    @classmethod
    def _if(cls):
        return 1

    @classmethod
    def braced_init(cls):
        return 1

    @classmethod
    def dfs(cls, v, e):
        return (
            cls._for(v) + v + 2
            + 3 + cls.braced_init()
            + cls._while(lambda i: 1, v)
            + v * (2 + 2 + cls._if())
            + e * (3 + 1 + 1)
            + cls._return()
        )

    @classmethod
    def get_path_from_dfs(cls, n):
        return (
            4 + 2 * cls.braced_init()
            + cls._while(lambda i: 3, n)
            + n * 2 * 4 * cls._if()
            + 2 * sp.Sum(cls._for(k) + (2 + cls._if()) * k, (k, 1, n)).doit()
            + 4 + 6 * n + cls._return()
        )

    @classmethod
    def get_supplies_to_collect(cls, p, s):
        return (
            1
            + cls._for(s) + s * (2 + cls.braced_init())
            + 1
            + cls._for(p) + p * (3 + cls._if() + 2 + cls.braced_init())
            + cls._return()
        )

    @classmethod
    def max(cls):
        return 2 + cls._return()

    @classmethod
    def get_path_length(cls, n):
        return (
            1
            + cls._for(n - 1) + 1
            + n * 5
            + cls._return()
        )

    @classmethod
    def reverse(cls, n):
        return (
            1 + cls.braced_init()
            + cls._for(n) + 1
            + n * 4
            + cls._return()
        )

    @classmethod
    def reconstruct_path(cls, n):
        return (
            1 + cls.braced_init()
            + cls._while(lambda i: 1, n)
            + n * 3
            + cls._return()
        )

    @classmethod
    def dijkstra(cls, v, e, p):
        return (
            4 + v + 1
            + cls._for(v) + 1 + v * 2
            + cls._while(lambda i: 1, v ** 2)
            + (v ** 2) * (3 + cls._if() + 2 + cls._if())
            + p * (1 + cls.reconstruct_path(v) + 3 + cls._if()) + cls._return()
            + e * (cls._for(e) + 1 + 2 + 4 + 5 + cls._if())
        )

    @classmethod
    def get_path_matrix(cls, v, e, p):
        return (
            1
            + cls._for(p + 1) + 1 + cls.braced_init()
            + (p + 1) * (2 + cls.dijkstra(v, e, p))
            + cls._return()
        )

    @classmethod
    def get_path_cost_matrix(cls, p, q):
        return (
            1
            + cls._for(p + 1) + 1
             + (p + 1) * (1 + 2 + cls._for(p + q) + (p + q) * (3 + cls.get_path_length(p + 2)))
        )

    @classmethod
    def dynamic_programming_recursive(cls, p, q, s, exact: bool):
        big_x_approx = p ** s / (sp.factorial(s-1)) + 1 # very close approximation for x >> s. Ideal for large facility if CRUDY-1 has small storage
        exact_sum = sp.Sum(p * sp.binomial(p - 1, k - 1), (k, 1, s)) + 1 # exact sum taken from OEIS A155865
        exact_hyp = sp.simplify(exact_sum.doit()) # with a 2F1. Closed form likely exists but is very slow to converge and is difficult to find if it does exist.
        exact_m_p = sp.simplify(exact_sum.subs(s, p).doit()) # if m == p. taken from OEIS A001787

        return (
            1 + cls.braced_init() + 1 + cls._if()
            + q * (1 + cls._if() + cls._for(q) + 3 + cls._if() + 2 + cls.braced_init())
            + (exact_hyp if exact else exact_m_p) * (
                2 + cls._if() + cls._for(p) + 1 + 2 + 2 + 4 + 1
                + cls._if() + 1 + 1 + cls.braced_init()
                + cls._for(p + 1) + (p + 1) * 1
                + 1 + cls.braced_init()
                + cls._return() + cls.braced_init()
            )
        )

    @classmethod
    def dynamic_programming(cls, p, q, s, exact: bool):
        return (
            1 + cls.dynamic_programming_recursive(p, q, s, exact)
            + 1 + cls.braced_init()
            + cls._for(p + 2)
            + (p + 2) * 1
            + cls._return()
        )

    @classmethod
    def get_F_path_from_H_path(cls, n, v):
        return (
            1 + cls.braced_init()
            + cls._for(n - 1) + 1
            + (6 + cls._for(v - 1) + 1 + (v - 1) * 2)
            + 3 + cls._return()
        )

    @classmethod
    def get_which_wing(cls, w):
        return (
            cls._for(w) + 1
            + w * (cls._if() + 2)
            + cls._return()
        )

    @classmethod
    def get_G_path_from_F_path(cls, v, n, w):
        return (
            1 + cls.braced_init()
            + cls._for(n - 1) + 2
            + (n - 1) * (2 + 3
                + 2 * (1 + cls.get_which_wing(w))
                + cls._if() + 1
                + cls.get_path_from_dfs(v) + 1
                + cls._for(v - 1) + 2 + v * 2
            )
            + 3 + cls._return()
        )

    @classmethod
    def get_F(cls, v, p, q, w, j):
        return (
            1 + cls._for(p + q + 1) + 2 + cls.braced_init()
            + (p + q + 1) * 1
            + 1 + cls._for(j) + 1
            + j * (2 + 2 + 3 + 2 * (3 + cls.braced_init()))
            + cls._for(w) + 1
            + (p + q + 1) * (1 + (p + q + 1 + cls._for(0) + 1) * (p + q + 1 + cls._for(0) + 1 + 1) * (6 + cls.get_path_from_dfs(v) + cls.get_path_length(v)))
            + w * 1 + cls._for(0) + 5 + cls.braced_init()
            + cls._return()
        )

    @classmethod
    def get_new_supply_storage(cls, n, p):
        return (
            1 + cls._for(n)
            + n * (cls._if() + 1) + p
            + 1 + cls._for(p)
            + p * (2 * cls._if() + 2 + 2 + 3)
            + cls._return()
        )

    @classmethod
    def ember_rescue(cls, v, e, w, j, p, q, s, *, exact: bool = False):
        return (
            1 + cls.get_supplies_to_collect(p, s)
            + 1 + cls._for(s)
            + s * (2 + cls._if() + 2)
            + cls.max() + 1 + 1
            + 1 + cls._for(w) + 1
            + w * (3 + cls._if() + 3 + cls.dfs(v, e))
            + 1 + cls.get_F(v, p, q, w, j)
            + 1 + cls.get_path_matrix(p + q + j + 1, e, p)
            + 1 + cls.get_path_cost_matrix(p, q)
            + 1 + cls.dynamic_programming(p, q, s, exact)
            + 1 + cls.get_F_path_from_H_path(p + 2, p + q + j + 1)
            + 1 + cls.get_G_path_from_F_path(v, p + q + j + 1, w)
            + 1 + cls.get_new_supply_storage(v, p)
            + cls._return() + cls._return()
        )


def main():
    n, m, w, j, p, q, s = sp.symbols("n,m,w,j,p,q,s", positive=True, integer=True)
    print(sp.latex(sp.simplify(Complexity.ember_rescue(n,m,w,j,p,q,s, exact=True), fraction=False)))
    print()
    print(sp.latex(sp.simplify(sp.O(Complexity.ember_rescue(n,m,w,j,p,q,s, exact=False), *[(x, oo) for x in [n, m, w, j, p, q, s]]))))



if __name__ == "__main__":
    main()