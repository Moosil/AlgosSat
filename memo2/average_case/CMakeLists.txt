cmake_minimum_required(VERSION 3.10)
project(average_cast)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(${PROJECT_NAME}
		${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/src/graph.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/src/ember_rescue.cpp
		${CMAKE_CURRENT_SOURCE_DIR}/include/graph.h
		${CMAKE_CURRENT_SOURCE_DIR}/include/ember_rescue.h
)

target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)