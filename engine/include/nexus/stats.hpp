/**
 * @file stats.hpp
 * @brief Estadísticas de captura en tiempo real.
 *
 * Contadores atómicos para uso thread-safe entre el hilo
 * de captura C++ y el hilo Python/Qt de lectura.
 */

#pragma once

#include "types.hpp"
#include <atomic>
#include <chrono>
#include <unordered_map>
#include <string>
#include <mutex>

namespace nexus {

/**
 * @brief Estadísticas de captura thread-safe con contadores atómicos.
 */
class CaptureStats {
public:
    CaptureStats() = default;

    // ── Contadores atómicos (thread-safe sin lock) ──

    /// Total de paquetes capturados
    std::atomic<uint64_t> total_packets{0};

    /// Total de bytes capturados
    std::atomic<uint64_t> total_bytes{0};

    /// Paquetes perdidos (ring buffer overflow)
    std::atomic<uint64_t> dropped_packets{0};

    /// Paquetes por segundo (calculado)
    std::atomic<double> packets_per_sec{0.0};

    /// Bytes por segundo (calculado)
    std::atomic<double> bytes_per_sec{0.0};

    // ── Distribución de protocolos (requiere mutex) ──

    /**
     * @brief Registra un paquete capturado para las estadísticas.
     * @param protocol Tipo de protocolo del paquete
     * @param bytes Tamaño del paquete en bytes
     */
    void record_packet(ProtocolType protocol, uint64_t bytes);

    /**
     * @brief Actualiza las métricas de velocidad (paquetes/seg, bytes/seg).
     * Debe llamarse periódicamente (ej: cada segundo).
     */
    void update_rates();

    /**
     * @brief Obtiene la distribución de protocolos como mapa {nombre → conteo}.
     */
    std::unordered_map<std::string, uint64_t> get_protocol_distribution() const;

    /**
     * @brief Reinicia todos los contadores.
     */
    void reset();

    /**
     * @brief Devuelve el uso de memoria estimado del motor (bytes).
     */
    [[nodiscard]] uint64_t estimated_memory_usage() const {
        return memory_usage_.load();
    }

    /**
     * @brief Actualiza el contador de memoria.
     */
    void update_memory_usage(uint64_t bytes) {
        memory_usage_.store(bytes);
    }

private:
    mutable std::mutex proto_mutex_;
    std::unordered_map<ProtocolType, uint64_t> protocol_counts_;

    std::atomic<uint64_t> memory_usage_{0};

    // Para calcular rates
    uint64_t prev_packets_ = 0;
    uint64_t prev_bytes_ = 0;
    std::chrono::steady_clock::time_point last_rate_update_ = std::chrono::steady_clock::now();
};

} // namespace nexus
