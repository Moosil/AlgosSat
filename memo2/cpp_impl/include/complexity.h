#pragma once

class Complexity {

public:
	inline static std::size_t operation_counter;

	static constexpr std::size_t return_ = 1;
	static constexpr std::size_t if_ = 1;
	static constexpr std::size_t braced_init = 1;
	static constexpr std::size_t while_inner = 1; // n * 1
	static constexpr std::size_t while_outer = 1; // + 1
	static constexpr std::size_t for_inner = 1; // n * 1
	static constexpr std::size_t for_outer = 1; // + 1
	static constexpr std::size_t get_edge_weight = 1;
	static constexpr std::size_t max = 3;

	static std::size_t get_neighbours([[maybe_unused]] std::size_t n) {
		return 1;
	}

	static std::size_t update_priority(const std::size_t n) {
		return static_cast<std::size_t>(std::ceil(std::log10(static_cast<double>(n))));
	}

	static std::size_t reverse(const std::size_t n) {
		return 1 + return_ + for_outer + 1 + n * (for_inner + 4);
	}
};