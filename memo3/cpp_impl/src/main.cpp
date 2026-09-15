#include <array>
#include <barkeep.h>
#include <fstream>

#include "ember_rescue.h"
#include "facility.h"
#include "complexity.h"

std::array<Graph::VertexT, 3> get_vertex_tuple(Graph::VertexT v);

int main() {
	constexpr std::size_t WING_TOTAL  = 15;
	constexpr std::size_t TRIAL_TOTAL = 100;

	std::size_t total{0};
	for (std::size_t wing_count = 1; wing_count <= WING_TOTAL; ++wing_count) {
		for (std::size_t exit_count = 1; exit_count <= wing_count; ++exit_count) {
			for (std::size_t supply_count = 1; supply_count <= wing_count; ++supply_count) {
				total += TRIAL_TOTAL * supply_count;
			}
		}
	}

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

	std::unordered_set<SupplyID> empty_set{};
	#pragma omp parallel for
	for (std::size_t wing_count = 1; wing_count <= WING_TOTAL; ++wing_count) {
		for (std::size_t exit_count = 1; exit_count <= wing_count; ++exit_count) {
			for (std::size_t supply_count = 1; supply_count <= wing_count; ++supply_count) {
				for (std::size_t supply_storage_size = 1; supply_storage_size <= supply_count; ++supply_storage_size) {
					for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
						Facility facility{
							static_cast<int>(trials + TRIAL_TOTAL * (
								                 wing_count + WING_TOTAL * (
									                 exit_count + wing_count * (
										                 supply_count + wing_count * supply_storage_size)))),
							wing_count,
							exit_count,
							supply_count
						};
						std::unordered_map<Graph::VertexT, SupplyID> vertex_to_supply_id;
						for (int        i = 1;
						     const auto s : facility.supplies) {
							vertex_to_supply_id[s] = ++i;
						}
						std::vector<SupplyID> supply_storage(supply_storage_size, 0);
						auto                  path = ember_rescue(
							std::make_pair(facility.wings, facility.junctions),
							facility.entry,
							facility.supplies,
							facility.exits,
							supply_storage,
							vertex_to_supply_id,
							empty_set
						);
						std::size_t v = 0, e = 0;
						for (const auto& wing : facility.wings) {
							v += wing.size();
							e += wing.get_edges().size();
						}
						data.push_back(
							std::to_string(v) + ',' +
							std::to_string(e) + ',' +
							std::to_string(wing_count) + ',' +
							std::to_string(facility.junctions.size()) + ',' +
							std::to_string(supply_count) + ',' +
							std::to_string(exit_count) + ',' +
							std::to_string(supply_storage_size) + ',' +
							std::to_string(trials) + ',' +
							std::to_string(Complexity::operation_counter)
						);
						++loops;
					}
				}
			}
		}
	}
	std::ofstream file{"data.txt", std::ios::binary};
	file << "v,e,w,j,p,q,s,t,op_count" << '\n';
	for (const auto& line : data) {
		file << line << '\n';
	}
	file.close();

	bar->done();

	return 0;
}

std::array<Graph::VertexT, 3> get_vertex_tuple(const Graph::VertexT v) {
	const auto low = static_cast<uint16_t>(v);
	return {v >> 16, low / Facility::WING_COLS, low % Facility::WING_COLS};
}
