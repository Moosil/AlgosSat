import numpy as np
import memo1a_algorithm

test_cases = [
	(np.array([[1],[2]]), np.array([[5], [10]]), np.array([[1]]), None, None, [5]),
	(np.array([[1,1,1,1],[1,-1,2,-1]]), np.array([[4],[2]]), np.array([[1],[3],[-1],[3]]), np.array([0, 1]), np.array([[3],[1],[0],[0]]), np.array([[0],[2],[2],[0]]))
]

def do_test_case(i: int, tuple_in) -> bool:
	A, b, c, B, initial, sol = tuple_in
	# simplex_sol = memo1a_algorithm._simplex(A, b, c, B, initial, np.linalg.inv(np.array([A[:, i] for i in B])))
	simplex_sol = memo1a_algorithm.simplex(A, b, c)
	if np.array_equal(simplex_sol, sol):
		print(f"Test case {i} {sol.transpose()[0]} succeeded")
	else:
		print(f"Test case {i} {sol.transpose()[0]} failed with {simplex_sol.transpose()[0]}")

for i, case in enumerate(test_cases):
	do_test_case(i, case)