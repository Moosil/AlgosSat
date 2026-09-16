#include <array>
#include <barkeep.h>
#include <fstream>

#include "ember_rescue.h"
#include "facility.h"
#include "complexity.h"

std::array<Graph::VertexT, 3> get_vertex_tuple(Graph::VertexT v);

int main() {
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

	std::unordered_set<SupplyID> empty_set{};
	#pragma omp parallel for
	for (std::size_t trials = 0; trials < TRIAL_TOTAL; ++trials) {
		Facility                                     facility{static_cast<int>(trials)};
		std::unordered_map<Graph::VertexT, SupplyID> vertex_to_supply_id;
		for (int        i = 1;
		     const auto s : facility.supplies) {
			vertex_to_supply_id[s] = ++i;
		}
		auto path = ember_rescue(
			std::make_pair(facility.wings, facility.junctions),
			facility.entry,
			facility.exits,
			facility.supplies,
			facility.weight,
			facility.value,
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
			std::to_string(facility.wings.size()) + ',' +
			std::to_string(facility.junctions.size()) + ',' +
			std::to_string(facility.supplies.size()) + ',' +
			std::to_string(facility.exits.size()) + ',' +
			std::to_string(trials) + ',' +
			std::to_string(Complexity::operation_counter)
		);
		++loops;
	}
	std::ofstream file{"data.txt", std::ios::binary};
	file << "v,e,w,j,p,q,t,op_count" << '\n';
	for (const auto& line : data) {
		file << line << '\n';
	}
	file.close();

	bar->done();

	return 0;
}