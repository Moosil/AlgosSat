This folder contains all the code for Memo1 Amendment 1

average_case/ contains the empirical-data-generating algorithm, implemented in c++ (it has its own README file)

average_tc.py was used to try and generate average-case empirical data, but *man* python is slow.

complexity.py is used to get the complexities of each function, and simplify them with sympy, a very cool python library

memo2a_algorithm.py is the updated (slightly) implementation in python

memo2_algorithm_test.py was used for generating data_facility.csv, which was unused, and for running text cases

memo2.py is the updated marimo file

memoisation_complexity_test.py was used while trying to figure out the memoised dp's operation count function, testing against the empirical data.

raw_pseudocode.txt is used to contain the pseudocode in the marimo file before it is formatted

references.txt is the references file, updated

each csv file contains data that could be or is used for visualisations in the marimo file:
- data_facility.csv was my attempt at caching the output of the T(n) formula
- data_facility_trials.csv was used for average case and was generated using a facility generating algorithm discussed above