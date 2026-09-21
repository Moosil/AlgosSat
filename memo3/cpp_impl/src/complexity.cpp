#include "complexity.h"

#include <cmath>
#include <ranges>

std::size_t Complexity::get_neighbours(std::size_t n) {
	return 1;
}

std::size_t Complexity::update_priority(const std::size_t n) {
	return static_cast<std::size_t>(std::ceil(std::log10(static_cast<double>(n))));
}

std::size_t Complexity::reverse(const std::size_t n) {
	return 1 + return_ + for_outer + 1 + n * (for_inner + 4);
}

void Complexity::add(const std::size_t amount) {
	op_count           += amount;
	#pragma omp atomic
	flame_graph[stack] += amount;
}

void Complexity::push_stack(const std::string& fn_name) {
	stack_depth++;
	if (stack_depth <= MAX_STACK_DEPTH) {
		stack.push_back(fn_name);
	}
}

void Complexity::pop_stack() {
	if (stack_depth <= MAX_STACK_DEPTH) {
		stack.pop_back();
	}
	stack_depth--;
}

std::size_t Complexity::get_op_count() const {
	return op_count;
}

void Complexity::reset_op_count() {
	stack       = {};
	stack_depth = 0;
	op_count    = 0;
}

void Complexity::reset_flame() {
	flame_graph = {};
}

std::string Complexity::get_flame() {
	std::string res_top;
	std::string res_bottom;
	std::string delim = "->";
	for (const auto& [k, v] : flame_graph) {
		res_top    += (k | std::views::join_with(delim) | std::ranges::to<std::string>()) + ',';
		res_bottom += std::to_string(v) + ',';
	}
	res_top.pop_back();
	res_bottom.pop_back();
	return res_top + '\n' + res_bottom;
}