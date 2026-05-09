#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

struct Scenario {
    std::string id;
    std::string zone;
    double speedKmh;
    double deceleration;
    double reactionSeconds;
    double limitMeters;
};

double brakingDistanceMeters(const Scenario& scenario) {
    const double speedMs = scenario.speedKmh / 3.6;
    const double reactionDistance = speedMs * scenario.reactionSeconds;
    const double brakingDistance = (speedMs * speedMs) / (2.0 * scenario.deceleration);
    return reactionDistance + brakingDistance;
}

std::string verdict(double distance, double limit) {
    return distance <= limit ? "PASS" : "FAIL";
}

int main() {
    const std::vector<Scenario> scenarios = {
        {"SIM-BRK-001", "A", 58.0, 1.15, 1.4, 235.0},
        {"SIM-BRK-002", "B", 72.0, 1.10, 1.5, 315.0},
        {"SIM-BRK-003", "C", 68.0, 0.92, 1.6, 245.0},
        {"SIM-BRK-004", "D", 42.0, 1.20, 1.2, 145.0},
    };

    std::ofstream output("generated/simulation-results.json");
    if (!output) {
        std::cerr << "Unable to write generated/simulation-results.json\n";
        return 1;
    }

    int failures = 0;
    output << "{\n";
    output << "  \"summary\": \"C++ braking model generated from speed, reaction time, deceleration, and zone limits.\",\n";
    output << "  \"scenarios\": [\n";

    for (std::size_t index = 0; index < scenarios.size(); ++index) {
        const Scenario& scenario = scenarios[index];
        const double distance = brakingDistanceMeters(scenario);
        const std::string result = verdict(distance, scenario.limitMeters);
        if (result == "FAIL") {
            failures += 1;
        }

        output << "    {\n";
        output << "      \"id\": \"" << scenario.id << "\",\n";
        output << "      \"zone\": \"" << scenario.zone << "\",\n";
        output << "      \"speedKmh\": " << scenario.speedKmh << ",\n";
        output << "      \"safeLimitMeters\": " << scenario.limitMeters << ",\n";
        output << "      \"computedDistanceMeters\": " << std::fixed << std::setprecision(2) << distance << ",\n";
        output << "      \"result\": \"" << result << "\"\n";
        output << "    }" << (index + 1 == scenarios.size() ? "\n" : ",\n");
    }

    output << "  ],\n";
    output << "  \"failedScenarios\": " << failures << "\n";
    output << "}\n";

    std::cout << "Generated simulation-results.json with " << failures << " failed scenario(s).\n";
    return failures == 0 ? 0 : 2;
}
