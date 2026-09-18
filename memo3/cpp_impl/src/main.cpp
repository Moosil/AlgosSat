#include <array>
#include <barkeep.h>
#include <print>
#include <fstream>

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
	std::ofstream file{"data.txt", std::ios::binary};
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

int main() {
	return test_trials();
}
