/**
 * @file stats.cpp
 * @brief Implementación de estadísticas de captura en tiempo real.
 */

#include "nexus/stats.hpp"

namespace nexus {

void CaptureStats::record_packet(ProtocolType protocol, uint64_t bytes) {
    total_packets.fetch_add(1, std::memory_order_relaxed);
    total_bytes.fetch_add(bytes, std::memory_order_relaxed);

    std::lock_guard<std::mutex> lock(proto_mutex_);
    protocol_counts_[protocol]++;
}

void CaptureStats::update_rates() {
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration<double>(now - last_rate_update_).count();

    if (elapsed < 0.1) return;  // Evitar divisiones por intervalos muy pequeños

    uint64_t current_packets = total_packets.load(std::memory_order_relaxed);
    uint64_t current_bytes = total_bytes.load(std::memory_order_relaxed);

    double pps = static_cast<double>(current_packets - prev_packets_) / elapsed;
    double bps = static_cast<double>(current_bytes - prev_bytes_) / elapsed;

    packets_per_sec.store(pps, std::memory_order_relaxed);
    bytes_per_sec.store(bps, std::memory_order_relaxed);

    prev_packets_ = current_packets;
    prev_bytes_ = current_bytes;
    last_rate_update_ = now;
}

std::unordered_map<std::string, uint64_t> CaptureStats::get_protocol_distribution() const {
    std::lock_guard<std::mutex> lock(proto_mutex_);
    std::unordered_map<std::string, uint64_t> result;

    for (const auto& [proto, count] : protocol_counts_) {
        result[protocol_to_string(proto)] = count;
    }

    return result;
}

void CaptureStats::reset() {
    total_packets.store(0, std::memory_order_relaxed);
    total_bytes.store(0, std::memory_order_relaxed);
    dropped_packets.store(0, std::memory_order_relaxed);
    packets_per_sec.store(0.0, std::memory_order_relaxed);
    bytes_per_sec.store(0.0, std::memory_order_relaxed);
    memory_usage_.store(0, std::memory_order_relaxed);

    prev_packets_ = 0;
    prev_bytes_ = 0;
    last_rate_update_ = std::chrono::steady_clock::now();

    std::lock_guard<std::mutex> lock(proto_mutex_);
    protocol_counts_.clear();
}

} // namespace nexus
