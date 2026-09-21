#include <array>
#include <barkeep.h>
#include <fstream>
#include <omp.h>
#include <print>
#include <ranges>

#include "complexity.h"
#include "ember_rescue.h"
#include "facility.h"

std::array<Graph::VertexT, 3> get_vertex_tuple(Graph::VertexT v);

int test_trials_small() {
	constexpr std::size_t TRIAL_TOTAL = 10000;

	std::size_t total{TRIAL_TOTAL};

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = total,
			.message    = "Analysing Facilities",
			.speed      = .5,
			.speed_unit = "facilities/s",
			.style      = barkeep::ProgressBarStyle::Bars,
			.interval   = 1.
		}
	);

	std::vector<std::string> data{};
	data.reserve(total);

	#pragma omp parallel for
	for (int trials = 0; trials < TRIAL_TOTAL; ++trials) {
		auto                                                complexity = std::make_shared<Complexity>();
		auto                                                drone      = Drone(complexity);
		std::size_t                                         seed       = trials;
		Facility                                            facility{static_cast<int>(seed), (seed % 3) + 2, 50, 2, 5};
		std::unordered_map<Graph::VertexT, Drone::SupplyID> vertex_to_supply_id;
		for (int        i = 1;
		     const auto s : facility.supplies) {
			vertex_to_supply_id[s] = ++i;
		}
		const auto budget = static_cast<std::size_t>(round(
			static_cast<float>(facility.full_budget) * .6
		));
		complexity->reset_op_count();
		const auto plan = drone.ember_rescue(
			std::make_pair(facility.wings, facility.junctions),
			facility.entry,
			facility.exits,
			facility.supplies,
			facility.weight,
			facility.value,
			budget,
			facility.drone_capacity,
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
			std::to_string(facility.drone_capacity) + ',' +
			std::to_string(budget_used) + ',' +
			std::to_string(budget) + ',' +
			std::to_string(value_collected) + ',' +
			std::to_string(value_total) + ',' +
			std::to_string(seed) + ',' +
			std::to_string(complexity->get_op_count())
		);
		++loops;
	} {
		std::ofstream file{"data_facility_small.csv", std::ios::binary};
		file <<
				"vertex count,edge count,wing count,junction count,supply count,exit count,supply cap,budget_used,budget,value_collected,value_total,seed,op_count"
				<< '\n';
		for (const auto& line : data) {
			file << line << '\n';
		}
		file.close();
	} {
		std::ofstream file{"flame_facility_small.csv", std::ios::binary};
		file << Complexity::get_flame();
		file.close();
	}

	bar->done();

	return 0;
}

int test_trials() {
	constexpr std::size_t TRIAL_TOTAL     = 25;
	constexpr std::size_t SUPPLY_TOTAL    = 60;
	constexpr std::size_t DRONE_CAP_TOTAL = 7;
	constexpr std::size_t WING_TOTAL      = 6;

	std::size_t total{0};
	for (int wing_count = WING_TOTAL; wing_count >= 1; --wing_count) {
		for (int exit_count = wing_count; exit_count >= 1; --exit_count) {
			total += TRIAL_TOTAL * (SUPPLY_TOTAL + 1) * (DRONE_CAP_TOTAL + 1) * 10;
		}
	}

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = total,
			.message    = "Analysing Facilities",
			.speed      = .5,
			.speed_unit = "facilities/s",
			.style      = barkeep::ProgressBarStyle::Bars,
			.interval   = 2.
		}
	);

	std::vector<std::string> data{};
	data.reserve(total);

	#pragma omp parallel for
	for (int wing_count = WING_TOTAL; wing_count >= 1; --wing_count) {
		auto complexity = std::make_shared<Complexity>();
		auto drone      = Drone(complexity);
		for (int exit_count = wing_count; exit_count >= 1; --exit_count) {
			for (int supply_count = SUPPLY_TOTAL; supply_count >= 0; --supply_count) {
				for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
					std::size_t seed = trials + TRIAL_TOTAL * (
						                   wing_count + WING_TOTAL * (
							                   exit_count + wing_count *
							                   supply_count));
					Facility facility{
						static_cast<int>(seed),
						static_cast<std::size_t>(wing_count),
						static_cast<std::size_t>(supply_count),
						static_cast<std::size_t>(exit_count),
						DRONE_CAP_TOTAL
					};
					std::size_t v = 0, e = 0;
					for (const auto& wing : facility.wings) {
						v += wing.size();
						e += wing.get_edges().size();
					}

					std::size_t value_total = 0;
					for (const Graph::VertexT x : facility.supplies) {
						value_total += facility.value.at(x);
					}

					std::unordered_map<Graph::VertexT, Drone::SupplyID> vertex_to_supply_id;
					for (int        i = 1;
					     const auto s : facility.supplies) {
						vertex_to_supply_id[s] = ++i;
					}
					for (int drone_cap = DRONE_CAP_TOTAL; drone_cap >= 0;
					     --drone_cap, --facility.drone_capacity, (drone_cap != -1) ? facility.set_budget() : void()) {
						for (int budget_percent = 1; budget_percent <= 10; budget_percent++) {
							const auto budget = static_cast<std::size_t>(round(
								static_cast<float>(facility.full_budget) * static_cast<float>(budget_percent) / 10
							));
							complexity->reset_op_count();
							const auto plan = drone.ember_rescue(
								std::make_pair(facility.wings, facility.junctions),
								facility.entry,
								facility.exits,
								facility.supplies,
								facility.weight,
								facility.value,
								budget,
								facility.drone_capacity,
								vertex_to_supply_id,
								{}
							);

							const auto& [supplies_collected, trip_costs, trip_supplies] = facility.get_plan_data(plan);

							std::size_t budget_used = 0;
							for (const std::size_t t : trip_costs) {
								budget_used += t;
							}

							std::size_t value_collected = 0;
							for (const Graph::VertexT x : supplies_collected) {
								value_collected += facility.value.at(x);
							}

							std::size_t collectable_value_total = 0;
							for (const Graph::VertexT x : facility.supplies) {
								if (const std::size_t val = facility.value.at(x);
									val <= drone_cap) {
									collectable_value_total += val;
								}
							}

							data.push_back(
								std::to_string(v) + ',' +
								std::to_string(e) + ',' +
								std::to_string(wing_count) + ',' +
								std::to_string(facility.junctions.size()) + ',' +
								std::to_string(supply_count) + ',' +
								std::to_string(exit_count) + ',' +
								std::to_string(drone_cap) + ',' +
								std::to_string(budget_used) + ',' +
								std::to_string(budget) + ',' +
								std::to_string(static_cast<float>(budget_percent) / 10) + ',' +
								std::to_string(value_collected) + ',' +
								std::to_string(value_total) + ',' +
								std::to_string(collectable_value_total) + ',' +
								std::to_string(seed) + ',' +
								std::to_string(complexity->get_op_count())
							);
							++loops;
						}
					}
				}
			}
		}
	} {
		std::ofstream file{"data_facility.csv", std::ios::binary};
		file << "vertex count,"
				<< "edge count,"
				<< "wing count,"
				<< "junction count,"
				<< "supply count,"
				<< "exit count,"
				<< "supply cap,"
				<< "budget used,"
				<< "budget,"
				<< "budget percent,"
				<< "value collected,"
				<< "value total,"
				<< "collectable value total,"
				<< "seed,"
				<< "op_count"
				<< '\n';
		for (const auto& line : data) {
			file << line << '\n';
		}
		file.close();
	} {
		std::ofstream file{"flame_facility.csv", std::ios::binary};
		file << Complexity::get_flame();
		file.close();
	}

	bar->done();

	return 0;
}

int test_one() {
	Facility                                            facility{0, 3, 50, 2, 5};
	std::unordered_map<Graph::VertexT, Drone::SupplyID> vertex_to_supply_id;
	for (int        i = 1;
	     const auto s : facility.supplies) {
		vertex_to_supply_id[s] = ++i;
	}
	const auto budget     = static_cast<std::size_t>(round(static_cast<float>(facility.full_budget) * .6));
	const auto complexity = std::make_shared<Complexity>();
	const auto drone      = Drone(complexity);
	const auto plan       = drone.ember_rescue(
		std::make_pair(facility.wings, facility.junctions),
		facility.entry,
		facility.exits,
		facility.supplies,
		facility.weight,
		facility.value,
		budget,
		facility.drone_capacity,
		vertex_to_supply_id,
		{}
	);

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
	constexpr std::size_t SUPPLY_TOTAL         = 60;
	constexpr std::size_t DRONE_CAP_TOTAL      = 10;
	constexpr std::size_t KNAPSACK_TRIAL_TOTAL = 64;

	constexpr std::size_t total = TRIAL_TOTAL * (SUPPLY_TOTAL + 1) * (DRONE_CAP_TOTAL + 1);

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = total,
			.message    = "Testing Approx knapsack",
			.speed      = .5,
			.speed_unit = "tests/s",
			.style      = barkeep::ProgressBarStyle::Bars,
			.interval   = 1.
		}
	);

	std::vector<std::string> data{};
	data.reserve(total);

	#pragma omp parallel for
	for (long long supply_n = SUPPLY_TOTAL; supply_n >= 0; --supply_n) {
		auto complexity = std::make_shared<Complexity>();
		auto drone      = Drone(complexity);
		for (long long drone_cap = DRONE_CAP_TOTAL; drone_cap >= 0; --drone_cap) {
			for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
				Facility facility{
					static_cast<int>(trials),
					5,
					static_cast<std::size_t>(supply_n),
					2,
					static_cast<std::size_t>(drone_cap)
				};
				const auto budget = static_cast<std::size_t>(round(static_cast<float>(facility.full_budget) * .6));


				const Graph flat_G = drone.flatten_graph(std::make_pair(facility.wings, facility.junctions));
				auto entry_prev = drone.dijkstra(flat_G, facility.entry);
				std::unordered_map<Graph::VertexT, std::vector<Graph::VertexT> > entry_paths{};
				for (const Graph::VertexT v : facility.supplies) {
					entry_paths[v] = drone.reconstruct_path(entry_prev, v);
				}

				std::size_t exit_run_cost = std::numeric_limits<std::size_t>::max();
				for (const Graph::VertexT e : facility.exits) {
					exit_run_cost = std::min(
						exit_run_cost,
						drone.get_path_length(flat_G, drone.reconstruct_path(entry_prev, e))
					);
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
						drone.get_weight_cost(
							facility.weight.at(v),
							drone_cap,
							drone.get_path_length(flat_G, entry_paths.at(v))
						)
					);
					supplies_ordered.push_back(v);
				}

				std::string res = std::format("{},{},{}", budget, supply_n, drone_cap);
				for (std::size_t i = 1; i <= KNAPSACK_TRIAL_TOTAL; ++i) {
					complexity->reset_op_count();
					res += ',' + std::to_string(
						std::get<1>(
							drone.knapsack_value(
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
					);
					res += ',' + std::to_string(complexity->get_op_count());
				}

				data.push_back(res);
				++loops;
			}
		}
	} {
		std::ofstream file{"data_knapsack.csv", std::ios::binary};
		file << "budget,supply,drone_cap";
		for (std::size_t i = 1; i <= KNAPSACK_TRIAL_TOTAL; i++) {
			file << std::format(",n={},op_{}", i, i);
		}
		file << '\n';
		for (const auto& line : data) {
			file << line << '\n';
		}
		file.close();
	} {
		std::ofstream file{"flame_knapsack.csv", std::ios::binary};
		file << Complexity::get_flame();
		file.close();
	}

	bar->done();

	return 0;
}

int main() {
	#ifdef _OPENMP
	std::println("OpenMP found. Max threads: {}", omp_get_max_threads());
	#else
	std::println("OpenMP not found.");
	return 1;
	#endif

	// Complexity::reset_flame();
	// test_trials_small();
	// Complexity::reset_flame();
	// test_knapsack();
	Complexity::reset_flame();
	test_trials();
	return 0;
}
