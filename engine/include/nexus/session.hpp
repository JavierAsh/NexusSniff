/**
 * @file session.hpp
 * @brief Sesión de captura con ring buffer lock-free.
 *
 * Gestiona el ciclo de vida de una sesión: nombre, interfaz,
 * timestamps y un ring buffer circular para almacenar paquetes
 * decodificados con mínimo overhead de sincronización.
 */

#pragma once

#include "packet.hpp"
#include "stats.hpp"
#include <vector>
#include <string>
#include <atomic>
#include <chrono>
#include <optional>

namespace nexus {

/**
 * @brief Ring buffer SPSC (Single Producer, Single Consumer) para paquetes.
 *
 * El hilo de captura C++ escribe (push) y el hilo Python lee (pop).
 * Usa índices atómicos para sincronización sin locks.
 */
class PacketRingBuffer {
public:
    /**
     * @brief Constructor con capacidad fija.
     * @param capacity Número máximo de paquetes en el buffer
     */
    explicit PacketRingBuffer(std::size_t capacity = DEFAULT_RING_BUFFER_SIZE);

    /**
     * @brief Intenta insertar un paquete en el buffer.
     * @param packet Paquete a insertar (movido)
     * @return true si se insertó, false si el buffer está lleno
     */
    bool try_push(PacketData&& packet);

    /**
     * @brief Intenta extraer un paquete del buffer.
     * @return El paquete si hay uno disponible, std::nullopt si está vacío
     */
    std::optional<PacketData> try_pop();

    /**
     * @brief Extrae hasta N paquetes del buffer de una vez.
     * @param max_count Máximo de paquetes a extraer
     * @return Vector con los paquetes extraídos
     */
    std::vector<PacketData> pop_batch(std::size_t max_count);

    /**
     * @brief Número de paquetes actualmente en el buffer.
     */
    [[nodiscard]] std::size_t size() const;

    /**
     * @brief Capacidad total del buffer.
     */
    [[nodiscard]] std::size_t capacity() const { return capacity_; }

    /**
     * @brief Indica si el buffer está vacío.
     */
    [[nodiscard]] bool empty() const { return size() == 0; }

    /**
     * @brief Limpia el buffer.
     */
    void clear();

private:
    std::vector<PacketData>  buffer_;
    std::size_t              capacity_;
    std::atomic<std::size_t> head_{0};  ///< Índice de escritura (producer)
    std::atomic<std::size_t> tail_{0};  ///< Índice de lectura (consumer)
};

/**
 * @brief Sesión de captura de paquetes.
 *
 * Contiene metadatos y el ring buffer para una captura activa.
 */
class CaptureSession {
public:
    /**
     * @brief Crea una nueva sesión de captura.
     * @param name Nombre descriptivo de la sesión
     * @param interface_name Nombre de la interfaz de red
     * @param bpf_filter Filtro BPF opcional
     * @param buffer_size Tamaño del ring buffer (paquetes)
     */
    CaptureSession(
        std::string name,
        std::string interface_name,
        std::string bpf_filter = "",
        std::size_t buffer_size = DEFAULT_RING_BUFFER_SIZE
    );

    // ── Accesores ──
    [[nodiscard]] const std::string& name() const { return name_; }
    [[nodiscard]] const std::string& interface_name() const { return interface_name_; }
    [[nodiscard]] const std::string& bpf_filter() const { return bpf_filter_; }
    [[nodiscard]] CaptureState state() const { return state_.load(); }

    // ── Ring buffer ──
    PacketRingBuffer& ring_buffer() { return ring_buffer_; }
    const PacketRingBuffer& ring_buffer() const { return ring_buffer_; }

    // ── Estadísticas ──
    CaptureStats& stats() { return stats_; }
    const CaptureStats& stats() const { return stats_; }

    // ── Ciclo de vida ──
    void mark_started();
    void mark_stopped();
    void mark_error(const std::string& error_msg);

    [[nodiscard]] const std::string& last_error() const { return last_error_; }

    /**
     * @brief Duración de la sesión en segundos.
     */
    [[nodiscard]] double duration_seconds() const;

private:
    std::string          name_;
    std::string          interface_name_;
    std::string          bpf_filter_;
    std::string          last_error_;
    std::atomic<CaptureState> state_{CaptureState::Idle};

    PacketRingBuffer     ring_buffer_;
    CaptureStats         stats_;

    std::chrono::steady_clock::time_point start_time_;
    std::chrono::steady_clock::time_point end_time_;
};

} // namespace nexus
