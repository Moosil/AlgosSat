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
	constexpr std::size_t TRIAL_TOTAL = 40000;

	constexpr std::size_t total{TRIAL_TOTAL * 2};

	std::size_t loops{0};

	auto bar = barkeep::ProgressBar(
		&loops,
		{
			.total      = total,
			.message    = "Analysing Facilities",
			.speed      = .5,
			.speed_unit = "facilities/s",
			.style      = barkeep::ProgressBarStyle::Bars,
			.interval   = .2
		}
	);

	std::vector<std::vector<std::string> > data{static_cast<std::size_t>(omp_get_max_threads())};
	for (auto& i : data) {
		i.reserve(total);
	}

	#pragma omp parallel for
	for (int trials = 0; trials < TRIAL_TOTAL; ++trials) {
		for (int budget_prop = 35; budget_prop <= 60; budget_prop += 60 - 35) {
			const int thread_number = omp_get_thread_num();

			auto complexity = std::make_shared<Complexity>();
			auto drone = Drone(complexity);
			std::size_t seed = trials;
			Facility facility{static_cast<int>(seed), (seed % 3) + 2, 50, 2, 5};
			std::unordered_map<Graph::VertexT, Drone::SupplyID> vertex_to_supply_id;
			for (int        i = 1;
			     const auto s : facility.supplies) {
				vertex_to_supply_id[s] = ++i;
			}
			const float budget_percent = static_cast<float>(budget_prop) / 100.f;
			const auto  budget         = static_cast<std::size_t>(round(
				static_cast<float>(facility.full_budget) * budget_percent
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

			std::size_t budget_used{0};
			for (const std::size_t t : trip_costs) {
				budget_used += t;
			}

			std::size_t value_collected{0};
			for (const Graph::VertexT x : supplies_collected) {
				value_collected += facility.value.at(x);
			}

			std::size_t value_total{0};
			for (const Graph::VertexT x : facility.supplies) {
				value_total += facility.value.at(x);
			}

			data[thread_number].push_back(
				std::to_string(v) + ',' +
				std::to_string(e) + ',' +
				std::to_string(facility.wings.size()) + ',' +
				std::to_string(facility.junctions.size()) + ',' +
				std::to_string(facility.supplies.size()) + ',' +
				std::to_string(facility.exits.size()) + ',' +
				std::to_string(facility.drone_capacity) + ',' +
				std::to_string(budget_used) + ',' +
				std::to_string(budget) + ',' +
				std::to_string(budget_prop) + ',' +
				std::to_string(value_collected) + ',' +
				std::to_string(value_total) + ',' +
				std::to_string(seed) + ',' +
				std::to_string(complexity->get_op_count())
			);
			#pragma omp atomic
			++loops;
		}
	} {
		std::ofstream file{"data_facility_small.csv", std::ios::binary};
		file <<
				"vertex count,"
				"edge count,"
				"wing count,"
				"junction count,"
				"supply count,"
				"exit count,"
				"supply cap,"
				"budget used,"
				"budget,"
				"budget percent,"
				"value collected,"
				"value total,"
				"seed,"
				"op count"
				<< '\n';
		for (const auto& lines : data) {
			for (const auto& line : lines) {
				file << line << '\n';
			}
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
	constexpr std::size_t TRIAL_TOTAL     = 5;
	constexpr std::size_t SUPPLY_TOTAL    = 75;
	constexpr std::size_t DRONE_CAP_TOTAL = 7;
	constexpr std::size_t WING_TOTAL      = 6;

	std::size_t total{0};
	for (int wing_count = WING_TOTAL; wing_count >= 1; --wing_count) {
		for (int exit_count = wing_count; exit_count >= 1; --exit_count) {
			total += TRIAL_TOTAL * (SUPPLY_TOTAL + 1 - 51) * (DRONE_CAP_TOTAL + 1) * 10;
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
			.interval   = .3
		}
	);

	std::vector<std::vector<std::string> > data{static_cast<std::size_t>(omp_get_max_threads())};

	#pragma omp parallel for schedule(guided, 1)
	for (int supply_count = SUPPLY_TOTAL; supply_count >= 51; --supply_count) {
		const int thread_number = omp_get_thread_num();
		auto      complexity    = std::make_shared<Complexity>();
		auto      drone         = Drone(complexity);
		for (int wing_count = WING_TOTAL; wing_count >= 1; --wing_count) {
			for (int exit_count = wing_count; exit_count >= 1; --exit_count) {
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
					     --drone_cap, --facility.drone_capacity) {
						facility.set_budget();
						for (int budget_prop = 1; budget_prop <= 10; budget_prop++) {
							const auto budget = static_cast<std::size_t>(round(
								static_cast<float>(facility.full_budget) * static_cast<float>(budget_prop) / 10
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

							std::size_t budget_used{0};
							for (const std::size_t t : trip_costs) {
								budget_used += t;
							}

							std::size_t value_collected{0};
							for (const Graph::VertexT x : supplies_collected) {
								value_collected += facility.value.at(x);
							}

							std::size_t collectable_value_total{0};
							for (const Graph::VertexT x : facility.supplies) {
								if (const std::size_t val = facility.value.at(x);
									val <= drone_cap) {
									collectable_value_total += val;
								}
							}

							data[thread_number].push_back(
								std::to_string(v) + ',' +
								std::to_string(e) + ',' +
								std::to_string(wing_count) + ',' +
								std::to_string(facility.junctions.size()) + ',' +
								std::to_string(supply_count) + ',' +
								std::to_string(exit_count) + ',' +
								std::to_string(drone_cap) + ',' +
								std::to_string(budget_used) + ',' +
								std::to_string(budget) + ',' +
								std::to_string(budget_prop * 10) + ',' +
								std::to_string(value_collected) + ',' +
								std::to_string(value_total) + ',' +
								std::to_string(collectable_value_total) + ',' +
								std::to_string(seed) + ',' +
								std::to_string(complexity->get_op_count())
							);
							#pragma omp atomic
							++loops;
						}
					}
				}
			}
		}
	} {
		std::ofstream file{"data_facility.csv", std::ios::binary};
		file << "vertex count,"
				"edge count,"
				"wing count,"
				"junction count,"
				"supply count,"
				"exit count,"
				"supply cap,"
				"budget used,"
				"budget,"
				"budget percent,"
				"value collected,"
				"value total,"
				"collectable value total,"
				"seed,"
				"op count"
				<< '\n';
		for (const auto& lines : data) {
			for (const auto& line : lines) {
				file << line << '\n';
			}
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

int main() {
	#ifdef _OPENMP
	std::println("OpenMP found. Max threads: {}", omp_get_max_threads());
	#else
	std::println("OpenMP not found.");
	return 1;
	#endif

	Complexity::reset_flame();
	test_trials_small();
	Complexity::reset_flame();
	test_trials();
	return 0;
}
