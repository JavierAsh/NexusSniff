/**
 * @file capturer.hpp
 * @brief Motor de captura de paquetes de red.
 *
 * Clase principal que orquesta la captura: lista interfaces,
 * abre handles Npcap, ejecuta el loop de captura en un hilo
 * dedicado, decodifica paquetes y los deposita en el ring buffer.
 */

#pragma once

#include "session.hpp"
#include "decoder.hpp"
#include "filter.hpp"
#include <string>
#include <vector>
#include <thread>
#include <functional>
#include <memory>

struct pcap;        // Forward declaration
typedef pcap pcap_t;

namespace nexus {

/**
 * @brief Información de una interfaz de red disponible.
 */
struct NetworkInterface {
    std::string name;           ///< Nombre del dispositivo (ej: \Device\NPF_{...})
    std::string description;    ///< Descripción humana (ej: "Ethernet")
    std::vector<std::string> addresses;  ///< Direcciones IP asociadas
    bool        is_loopback = false;
};

/**
 * @brief Motor de captura de paquetes de red.
 *
 * Uso típico:
 * @code
 * PacketCapturer capturer;
 * auto ifaces = capturer.list_interfaces();
 * capturer.start(ifaces[0].name, "tcp port 80");
 * // ... leer paquetes del ring buffer ...
 * capturer.stop();
 * @endcode
 */
class PacketCapturer {
public:
    PacketCapturer();
    ~PacketCapturer();

    // No copiable
    PacketCapturer(const PacketCapturer&) = delete;
    PacketCapturer& operator=(const PacketCapturer&) = delete;

    /**
     * @brief Enumera todas las interfaces de red disponibles en el sistema.
     * @return Vector de interfaces con nombre, descripción y direcciones
     * @throws std::runtime_error si Npcap no está instalado
     */
    static std::vector<NetworkInterface> list_interfaces();

    /**
     * @brief Inicia la captura de paquetes en una interfaz.
     * @param interface_name Nombre de la interfaz (de list_interfaces())
     * @param bpf_filter Filtro BPF opcional (ej: "tcp port 80")
     * @param snap_len Bytes máximos a capturar por paquete
     * @param buffer_size Tamaño del ring buffer (paquetes)
     * @return true si la captura se inició correctamente
     */
    bool start(
        const std::string& interface_name,
        const std::string& bpf_filter = "",
        int snap_len = DEFAULT_SNAP_LEN,
        std::size_t buffer_size = DEFAULT_RING_BUFFER_SIZE
    );

    /**
     * @brief Detiene la captura activa.
     */
    void stop();

    /**
     * @brief Indica si hay una captura activa.
     */
    [[nodiscard]] bool is_capturing() const;

    /**
     * @brief Obtiene paquetes del ring buffer (batch).
     * @param max_count Máximo de paquetes a obtener
     * @return Vector de paquetes decodificados
     */
    std::vector<PacketData> get_packets(std::size_t max_count = 256);

    /**
     * @brief Obtiene las estadísticas actuales de captura.
     */
    [[nodiscard]] const CaptureStats& get_stats() const;

    /**
     * @brief Obtiene el último error.
     */
    [[nodiscard]] std::string get_last_error() const;

    /**
     * @brief Obtiene información de la sesión activa.
     */
    [[nodiscard]] CaptureSession* get_session() { return session_.get(); }

private:
    /**
     * @brief Función del hilo de captura.
     * Loop principal: pcap_next_ex → decode → ring buffer.
     */
    void capture_loop();

    pcap_t*                          handle_ = nullptr;
    BpfFilter                        filter_;
    std::unique_ptr<CaptureSession>  session_;
    std::thread                      capture_thread_;
    std::atomic<bool>                should_stop_{false};
    std::string                      last_error_;
    uint64_t                         packet_counter_ = 0;
};

} // namespace nexus
