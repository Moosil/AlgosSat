Idk how familiar you are with C++, but I'm sure you known it's much faster than Python.

This code is identical to the one in average_tc.py (some implementation differences because C++ is more picky)

It runs ~100x faster, which is pretty good I would say. The only 3rd party library used was for a nice progress bar, everything else is just standard libraries (C++26).

include/ contains the header files: like function signatures, constant variables, class structures

src/ contains the source files: implementations of the functions

src/main.cpp is the entry point, with a lovely 4 nested for loop to get a **bunch** of cases for the empirical data.

*/complexity.h/cpp contains the complexity constants of certain ADT functions, as well as looping and control flow functions.

*/ember_rescue.h/cpp contains the implementations of the algorithm, with a singleton (global-scoped static variable) which contains the number of operations performed in the running of the algorithm. I put it in the Complexity class in complexity.h (the singleton).

*/facility.h/cpp is a extension of your facility generating algorithm which allows for variable numbers of supplies, exits and wings. It does **not** cover all possible problem instances, just ones similar to facilities we've encountered.

*/graph.h/cpp is a simple graph class, only the operations needed, adjacency list (since vertex_t is not a zero-indexed integer, it isn't very cache friendly, showing that I did not optimise **at all**).