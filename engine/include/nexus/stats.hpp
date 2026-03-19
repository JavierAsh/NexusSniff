/**
 * @file stats.hpp
 * @brief Estadísticas de captura en tiempo real — 100% lock-free.
 *
 * Todos los contadores usan std::atomic para acceso thread-safe
 * sin necesidad de mutex, eliminando cualquier contención entre
 * el hilo de captura C++ y el hilo Python/Qt de lectura.
 */

#pragma once

#include "types.hpp"
#include <atomic>
#include <chrono>
#include <unordered_map>
#include <string>
#include <array>

namespace nexus {

/**
 * @brief Número total de protocolos conocidos en ProtocolType.
 * Debe coincidir con el número de valores en el enum class ProtocolType.
 */
inline constexpr std::size_t PROTOCOL_COUNT = 16;

/**
 * @brief Estadísticas de captura 100% lock-free con contadores atómicos.
 *
 * En lugar de un std::unordered_map<ProtocolType, uint64_t> protegido
 * por mutex, utiliza un std::array<std::atomic<uint64_t>, PROTOCOL_COUNT>
 * indexado por el valor numérico del enum ProtocolType.
 */
class CaptureStats {
public:
    CaptureStats() {
        // Inicializar todos los contadores de protocolo a 0
        for (auto& counter : protocol_counts_) {
            counter.store(0, std::memory_order_relaxed);
        }
    }

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

    // ── Distribución de protocolos (lock-free) ──

    /**
     * @brief Registra un paquete capturado — completamente lock-free.
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
     * Lectura lock-free: lee cada atomic individualmente.
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
    /// Contadores de protocolo lock-free indexados por ProtocolType
    std::array<std::atomic<uint64_t>, PROTOCOL_COUNT> protocol_counts_;

    std::atomic<uint64_t> memory_usage_{0};

    // Para calcular rates (solo accedidos desde update_rates)
    uint64_t prev_packets_ = 0;
    uint64_t prev_bytes_ = 0;
    std::chrono::steady_clock::time_point last_rate_update_ = std::chrono::steady_clock::now();
};

} // namespace nexus
