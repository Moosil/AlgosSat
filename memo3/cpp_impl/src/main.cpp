#include <array>
#include <barkeep.h>
#include <print>
#include <fstream>
#include <ranges>

#include "ember_rescue.h"
#include "facility.h"
#include "complexity.h"

std::array<Graph::VertexT, 3> get_vertex_tuple(Graph::VertexT v);

int test_trials() {
	constexpr std::size_t TRIAL_TOTAL = 100;

	std::size_t total{TRIAL_TOTAL};

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = total,
			.message    = "Analysing Facilities",
			.speed      = .8,
			.speed_unit = "facilities/s",
			.style      = barkeep::ProgressBarStyle::Bars,
		}
	);

	std::vector<std::string> data{};
	data.reserve(total);

	//#pragma omp parallel for
	for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
		Facility                                     facility{static_cast<int>(trials)};
		std::unordered_map<Graph::VertexT, SupplyID> vertex_to_supply_id;
		for (int        i = 1;
		     const auto s : facility.supplies) {
			vertex_to_supply_id[s] = ++i;
		}
		const auto budget = static_cast<std::size_t>(round(static_cast<float>(facility.full_budget) * .6));
		const auto plan   = ember_rescue(
			std::make_pair(facility.wings, facility.junctions),
			facility.entry,
			facility.exits,
			facility.supplies,
			facility.weight,
			facility.value,
			budget,
			vertex_to_supply_id,
			{}
		);
		std::size_t v = 0, e = 0;
		for (const auto& wing : facility.wings) {
			v += wing.size();
			e += wing.get_edges().size();
		}

		const auto& [supplies_collected, trip_costs, trip_supplies] = facility.get_plan_data(plan);

		std::size_t budget_used = 0;
		for (const std::size_t t : trip_costs) {
			budget_used += t;
		}

		std::size_t value_collected = 0;
		for (const Graph::VertexT x : supplies_collected) {
			value_collected += facility.value.at(x);
		}

		std::size_t value_total = 0;
		for (const Graph::VertexT x : facility.supplies) {
			value_total += facility.value.at(x);
		}

		data.push_back(
			std::to_string(v) + ',' +
			std::to_string(e) + ',' +
			std::to_string(facility.wings.size()) + ',' +
			std::to_string(facility.junctions.size()) + ',' +
			std::to_string(facility.supplies.size()) + ',' +
			std::to_string(facility.exits.size()) + ',' +
			std::to_string(budget_used) + ',' +
			std::to_string(budget) + ',' +
			std::to_string(value_collected) + ',' +
			std::to_string(value_total) + ',' +
			std::to_string(trials) + ',' +
			std::to_string(Complexity::operation_counter)
		);
		++loops;
	}
	std::ofstream file{"data_facility.csv", std::ios::binary};
	file << "v,e,w,j,p,q,budget_used,budget,value_collected,value_total,t,op_count" << '\n';
	for (const auto& line : data) {
		file << line << '\n';
	}
	file.close();

	bar->done();

	return 0;
}

int test_one() {
	Facility                                     facility{0};
	std::unordered_map<Graph::VertexT, SupplyID> vertex_to_supply_id;
	for (int        i = 1;
	     const auto s : facility.supplies) {
		vertex_to_supply_id[s] = ++i;
	}
	const auto budget = static_cast<std::size_t>(round(static_cast<float>(facility.full_budget) * .6));
	auto       plan   = ember_rescue(
		std::make_pair(facility.wings, facility.junctions),
		facility.entry,
		facility.exits,
		facility.supplies,
		facility.weight,
		facility.value,
		budget,
		vertex_to_supply_id,
		{}
	);
	// for (const auto& [vertex, instruction, weight, value] : plan) {
	// 	const auto [w, c, r] = Facility::get_vertex_tuple(vertex);
	// 	std::println("(({}, {}, {}), {}, {}, {})", w, c, r, instruction, weight, value);
	// }

	const auto& [supplies_collected, trip_costs, trip_supplies] = facility.get_plan_data(plan);

	std::size_t budget_used = 0;
	for (const std::size_t t : trip_costs) {
		budget_used += t;
	}

	std::size_t value_collected = 0;
	for (const Graph::VertexT v : supplies_collected) {
		value_collected += facility.value.at(v);
	}

	std::size_t total_value = 0;
	for (const Graph::VertexT v : facility.supplies) {
		total_value += facility.value.at(v);
	}

	facility.print();
	std::println("budget used: {}/{}", budget_used, budget);
	std::println("supplies collected: {}/{}", supplies_collected.size(), facility.supplies.size());
	std::println("value collected: {}/{}", value_collected, total_value);
	return 0;
}

int test_knapsack() {
	constexpr std::size_t TRIAL_TOTAL          = 100;
	constexpr std::size_t KNAPSACK_TRIAL_TOTAL = 50;

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = TRIAL_TOTAL,
			.message    = "Testing Approx knapsack",
			.speed      = .8,
			.speed_unit = "tests/s",
			.style      = barkeep::ProgressBarStyle::Bars,
		}
	);

	std::vector<std::string> data{};
	data.reserve(TRIAL_TOTAL);

	#pragma omp parallel for
	for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
		Facility   facility{static_cast<int>(trials)};
		const auto budget = static_cast<std::size_t>(round(static_cast<float>(facility.full_budget) * .6));


		const Graph flat_G = flatten_graph(std::make_pair(facility.wings, facility.junctions));
		auto entry_prevs = dijkstra(flat_G, facility.entry);
		std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > entry_paths{};
		for (const Graph::VertexT v : facility.supplies) {
			entry_paths[v] = reconstruct_path(entry_prevs, v);
		}

		std::size_t exit_run_cost = std::numeric_limits<std::size_t>::max();
		for (const Graph::VertexT e : facility.exits) {
			exit_run_cost = std::min(exit_run_cost, get_path_length(flat_G, reconstruct_path(entry_prevs, e)));
		}

		std::vector<Graph::VertexT> supplies_ordered{};
		supplies_ordered.reserve(facility.supplies.size());
		std::vector<std::size_t> supply_value_ordered{};
		supply_value_ordered.reserve(facility.supplies.size());
		std::vector<std::size_t> supply_cost_ordered{};
		supply_cost_ordered.reserve(facility.supplies.size());

		for (const Graph::VertexT v : facility.supplies) {
			supply_value_ordered.push_back(facility.value.at(v));
			supply_cost_ordered.push_back(
				get_weight_cost(facility.weight.at(v), get_path_length(flat_G, entry_paths.at(v)))
			);
			supplies_ordered.push_back(v);
		}

		std::string res = std::to_string(budget) + ',';
		for (std::size_t i = 1; i <= KNAPSACK_TRIAL_TOTAL; ++i) {
			Complexity::operation_counter = 0;
			res                           += std::to_string(
				std::get<1>(
					knapsack(
						budget / i + (budget % i != 0),
						supply_value_ordered,
						std::views::transform(
							supply_cost_ordered,
							[i](const std::size_t x) -> std::size_t {
								return x / i + (x % i != 0);
							}
						) | std::ranges::to<std::vector>()
					)
				)
			) + ',';
			res += std::to_string(Complexity::operation_counter) + ',';
		}
		res.pop_back();

		data.push_back(res);
		++loops;
	}
	std::ofstream file{"data_knapsack.csv", std::ios::binary};
	file << "budget";
	for (std::size_t i = 1; i <= KNAPSACK_TRIAL_TOTAL; i++) {
		file << std::format(",n={},op_{}", i, i);
	}
	file << '\n';
	for (const auto& line : data) {
		file << line << '\n';
	}
	file.close();

	bar->done();

	return 0;
}

int main() {
	return test_trials();
}
