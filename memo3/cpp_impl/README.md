A C++ implantation of the algorithm

include/ contains the header files (*.h)
- complexity.h is used for tracking number of operations
- ember_rescue.h contains the c++ implementation of the algorithm
- facility.h contains an implementation of the facility generator used in the template marimo file
- graph.h is a graph implementation using graaf

src/ contains the source files (*.cpp)
- all of the above but implementing them
- main.cpp is the entry point and parallelises data generation with OpenMP

CMakeLists.txt is used for CMake builds
