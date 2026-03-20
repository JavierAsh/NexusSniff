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
     * 
     * @return {std::vector<NetworkInterface>} Vector de interfaces con nombre, descripción y direcciones.
     * @throws {std::runtime_error} Si el servicio Npcap no está instalado o en ejecución.
     * 
     * @example
     * std::vector<NetworkInterface> devs = PacketCapturer::list_interfaces();
     * for (const auto& dev : devs) { std::cout << dev.name; }
     */
    static std::vector<NetworkInterface> list_interfaces();

    /**
     * @brief Inicia la captura de paquetes en una interfaz específica.
     * 
     * @param {std::string} interface_name Nombre de la interfaz (devuelto por list_interfaces()).
     * @param {std::string} bpf_filter Filtro de Berkeley Packet Filter opcional.
     * @param {int} snap_len Cantidad máxima de bytes a capturar por paquete.
     * @param {std::size_t} buffer_size Tamaño del ring buffer en paquetes.
     * 
     * @return {bool} `true` si la captura inició exitosamente con el hilo levantado.
     * @throws {std::invalid_argument} Si el nombre de la interfaz está vacío.
     * 
     * @example
     * PacketCapturer cap;
     * cap.start("\\Device\\NPF_{...}", "tcp port 80", 65535, 10000);
     */
    bool start(
        const std::string& interface_name,
        const std::string& bpf_filter = "",
        int snap_len = DEFAULT_SNAP_LEN,
        std::size_t buffer_size = DEFAULT_RING_BUFFER_SIZE
    );

    /**
     * @brief Detiene la captura activa de forma segura.
     * 
     * Finaliza el hilo de captura y cierra el handle de Npcap. No lanza excepciones.
     * 
     * @example
     * cap.stop();
     */
    void stop();

    /**
     * @brief Indica si hay una captura activa.
     */
    [[nodiscard]] bool is_capturing() const;

    /**
     * @brief Extrae un lote de paquetes decodificados desde el ring buffer.
     * 
     * @param {std::size_t} max_count Cantidad máxima de paquetes a extraer en esta llamada.
     * @return {std::vector<PacketData>} Vector que contiene entre 0 y `max_count` paquetes.
     * 
     * @example
     * auto batch = cap.get_packets(500);
     * for (const auto& pkt : batch) { process(pkt); }
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
