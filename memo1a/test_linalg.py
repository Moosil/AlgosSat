import numpy as np
import memo1a_algorithm

test_cases = [
	(np.array([[1,1,1,1],[1,-1,2,-1]]), np.array([[4],[2]]), np.array([[1],[3],[-1],[3]]), np.array([0, 1]), np.array([[3],[1],[0],[0]]), np.array([0,2,2,0]))
]

def do_test_case(tuple_in) -> bool:
	A, b, c, B, initial, sol = tuple_in
	return np.array_equal(memo1a_algorithm.simplex(A, b, c, B, initial, np.linalg.inv(np.array([A[:, i] for i in B]))), sol)

for i, case in enumerate(test_cases):
	print(f"Test case {i} = [0 2 2 0]: {do_test_case(case)}")