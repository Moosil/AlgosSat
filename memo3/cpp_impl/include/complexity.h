#pragma once
#include <ranges>
#include <string>

class Complexity {
public:
	static constexpr std::size_t return_         = 1;
	static constexpr std::size_t if_             = 1;
	static constexpr std::size_t braced_init     = 1;
	static constexpr std::size_t while_inner     = 1; // n * 1
	static constexpr std::size_t while_outer     = 1; // + 1
	static constexpr std::size_t for_inner       = 1; // n * 1
	static constexpr std::size_t for_outer       = 1; // + 1
	static constexpr std::size_t break_          = 1;
	static constexpr std::size_t get_edge_weight = 1;
	static constexpr std::size_t max             = 3;

	static std::size_t get_neighbours([[maybe_unused]] std::size_t n) {
		return 1;
	}

	static std::size_t update_priority(const std::size_t n) {
		return static_cast<std::size_t>(std::ceil(std::log10(static_cast<double>(n))));
	}

	static std::size_t reverse(const std::size_t n) {
		return 1 + return_ + for_outer + 1 + n * (for_inner + 4);
	}

	static void add(const std::size_t amount) {
		op_count           += amount;
		flame_graph[stack] += amount;
	}

	static void push_stack(const std::string& fn_name) {
		stack_depth++;
		if (stack_depth <= MAX_STACK_DEPTH) {
			stack.push_back(fn_name);
		}
	}

	static void pop_stack() {
		if (stack_depth <= MAX_STACK_DEPTH) {
			stack.pop_back();
		}
		stack_depth--;
	}

	static std::size_t get_op_count() {
		return op_count;
	}

	static void reset_op_count() {
		stack       = {};
		stack_depth = 0;
		op_count    = 0;
	}

	static void reset_flame() {
		flame_graph = {};
	}

	static std::string get_flame() {
		std::string res_top;
		std::string res_bottom;
		std::string delim = "->";
		for (const auto& [k, v] : flame_graph) {
			res_top    += (k | std::views::join_with(delim) | std::ranges::to<std::string>()) + ';';
			res_bottom += std::to_string(v) + ';';
		}
		res_top.pop_back();
		res_bottom.pop_back();
		return res_top + '\n' + res_bottom;
	}

private:
	constexpr static std::size_t MAX_STACK_DEPTH = 7;
	inline static std::size_t    op_count;

	inline static std::map<std::vector<std::string>, std::size_t> flame_graph{};
	inline static std::vector<std::string>                        stack{};
	inline static std::size_t                                     stack_depth = 0;
};