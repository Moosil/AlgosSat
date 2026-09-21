#pragma once

#include <map>
#include <string>
#include <vector>

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

	static std::size_t get_neighbours([[maybe_unused]] std::size_t n);

	static std::size_t update_priority(std::size_t n);

	static std::size_t reverse(std::size_t n);

	void add(std::size_t amount);

	void push_stack(const std::string& fn_name);

	void pop_stack();

	[[nodiscard]] std::size_t get_op_count() const;

	void reset_op_count();

	static void reset_flame();

	static std::string get_flame();

private:
	static constexpr std::size_t MAX_STACK_DEPTH = 7;
	std::size_t                  op_count{0};

	static inline std::map<std::vector<std::string>, std::size_t> flame_graph{};
	std::vector<std::string>                                      stack{};
	std::size_t                                                   stack_depth = 0;
};