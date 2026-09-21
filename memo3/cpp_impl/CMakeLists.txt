cmake_minimum_required(VERSION 3.10)
project(Memo3Cpp)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenMP REQUIRED)

add_executable(${PROJECT_NAME}
		${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/src/graph.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/include/graph.h
		${CMAKE_CURRENT_SOURCE_DIR}/src/ember_rescue.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/include/ember_rescue.h
		${CMAKE_CURRENT_SOURCE_DIR}/src/facility.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/include/facility.h
		${CMAKE_CURRENT_SOURCE_DIR}/src/complexity.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/include/complexity.h
		${CMAKE_CURRENT_SOURCE_DIR}/../../third_party/barkeep/barkeep/barkeep.h
)

target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include ${CMAKE_CURRENT_SOURCE_DIR}/../../third_party/barkeep/barkeep)

target_link_libraries(${PROJECT_NAME} PRIVATE OpenMP::OpenMP_CXX)

target_compile_options(${PROJECT_NAME} PUBLIC
		"$<$<CONFIG:Release>:/O2>"
		"$<$<CONFIG:Release>:/Ob3>"
		"$<$<CONFIG:Release>:/GA>"
		"$<$<CONFIG:Release>:/GL>"
		"$<$<CONFIG:Release>:/Gy>"
		"$<$<CONFIG:Release>:/GS->"
		"$<$<CONFIG:Release>:/sdl->"
		"$<$<CONFIG:Release>:/permissive->"
		"$<$<CONFIG:Release>:/fp:fast>"
		"$<$<CONFIG:Release>:/arch:AVX512>"
		"$<$<CONFIG:Release>:/Qfast_transcendentals>"
		"$<$<CONFIG:Release>:/openmp:llvm>"
		
		"$<$<CONFIG:Debug>:/PROFILE>"
)

target_link_options(${PROJECT_NAME} PUBLIC
		"$<$<CONFIG:Release>:/INCREMENTAL:NO>"
		"$<$<CONFIG:Release>:/OPT:ICF>"
		"$<$<CONFIG:Release>:/OPT:REF>"
		"$<$<CONFIG:Release>:/MANIFEST:NO>"
)

set(CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE)