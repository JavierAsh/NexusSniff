/**
 * @file stats.cpp
 * @brief Implementación de estadísticas de captura — 100% lock-free.
 *
 * Todas las operaciones usan std::atomic, eliminando cualquier
 * contención de mutex entre hilos de captura y lectura.
 */

#include "nexus/stats.hpp"

namespace nexus {

void CaptureStats::record_packet(ProtocolType protocol, uint64_t bytes) {
    total_packets.fetch_add(1, std::memory_order_relaxed);
    total_bytes.fetch_add(bytes, std::memory_order_relaxed);

    // Incremento lock-free del contador de protocolo
    auto index = static_cast<std::size_t>(protocol);
    if (index < PROTOCOL_COUNT) {
        protocol_counts_[index].fetch_add(1, std::memory_order_relaxed);
    }
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
    // Lectura lock-free: cada load() es atómico independiente
    std::unordered_map<std::string, uint64_t> result;

    for (std::size_t i = 0; i < PROTOCOL_COUNT; ++i) {
        uint64_t count = protocol_counts_[i].load(std::memory_order_relaxed);
        if (count > 0) {
            result[protocol_to_string(static_cast<ProtocolType>(i))] = count;
        }
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

    // Reset lock-free de todos los contadores de protocolo
    for (auto& counter : protocol_counts_) {
        counter.store(0, std::memory_order_relaxed);
    }
}

} // namespace nexus
