/**
 * @file capturer.cpp
 * @brief Implementación del motor de captura de paquetes.
 *
 * Gestiona el ciclo completo: abrir interfaz con Npcap,
 * hilo de captura, decodificación y ring buffer.
 */

#include "nexus/capturer.hpp"
#include <pcap.h>
#include <stdexcept>
#include <cstring>

#ifdef _WIN32
    #include <winsock2.h>
    #include <iphlpapi.h>
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "iphlpapi.lib")
#endif

namespace nexus {

// ══════════════════════════════════════════════════════════════
// Constructor / Destructor
// ══════════════════════════════════════════════════════════════

PacketCapturer::PacketCapturer() {
#ifdef _WIN32
    // Inicializar Winsock (requerido para ntohs/ntohl en Windows)
    WSADATA wsa_data;
    WSAStartup(MAKEWORD(2, 2), &wsa_data);
#endif
}

PacketCapturer::~PacketCapturer() {
    stop();
#ifdef _WIN32
    WSACleanup();
#endif
}

// ══════════════════════════════════════════════════════════════
// Enumeración de interfaces
// ══════════════════════════════════════════════════════════════

std::vector<NetworkInterface> PacketCapturer::list_interfaces() {
    pcap_if_t* all_devs = nullptr;
    char errbuf[PCAP_ERRBUF_SIZE];

    if (pcap_findalldevs(&all_devs, errbuf) == -1) {
        throw std::runtime_error(
            std::string("Error enumerando interfaces (¿Npcap instalado?): ") + errbuf
        );
    }

    std::vector<NetworkInterface> interfaces;

    for (pcap_if_t* dev = all_devs; dev != nullptr; dev = dev->next) {
        NetworkInterface iface;
        iface.name = dev->name ? dev->name : "";
        iface.description = dev->description ? dev->description : "(Sin descripción)";
        iface.is_loopback = (dev->flags & PCAP_IF_LOOPBACK) != 0;

        // Extraer direcciones IP
        for (pcap_addr_t* addr = dev->addresses; addr != nullptr; addr = addr->next) {
            if (addr->addr && addr->addr->sa_family == AF_INET) {
                auto* sockaddr_in = reinterpret_cast<struct sockaddr_in*>(addr->addr);
                char ip_str[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &sockaddr_in->sin_addr, ip_str, sizeof(ip_str));
                iface.addresses.emplace_back(ip_str);
            }
        }

        interfaces.push_back(std::move(iface));
    }

    pcap_freealldevs(all_devs);
    return interfaces;
}

// ══════════════════════════════════════════════════════════════
// Inicio / Detención de captura
// ══════════════════════════════════════════════════════════════

bool PacketCapturer::start(
    const std::string& interface_name,
    const std::string& bpf_filter,
    int snap_len,
    std::size_t buffer_size
) {
    // Detener captura anterior si existe
    stop();

    char errbuf[PCAP_ERRBUF_SIZE];

    // Abrir la interfaz con Npcap
    handle_ = pcap_open_live(
        interface_name.c_str(),
        snap_len,
        1,  // modo promiscuo
        DEFAULT_READ_TIMEOUT_MS,
        errbuf
    );

    if (!handle_) {
        last_error_ = std::string("Error abriendo interfaz: ") + errbuf;
        return false;
    }

    // Verificar que sea Ethernet (DLT_EN10MB)
    if (pcap_datalink(handle_) != DLT_EN10MB) {
        last_error_ = "La interfaz seleccionada no es Ethernet.";
        pcap_close(handle_);
        handle_ = nullptr;
        return false;
    }

    // Aplicar filtro BPF si se proporcionó
    if (!bpf_filter.empty()) {
        if (!filter_.apply(handle_, bpf_filter)) {
            last_error_ = filter_.last_error();
            pcap_close(handle_);
            handle_ = nullptr;
            return false;
        }
    }

    // Crear sesión
    session_ = std::make_unique<CaptureSession>(
        "Captura", interface_name, bpf_filter, buffer_size
    );
    session_->mark_started();

    // Iniciar hilo de captura
    should_stop_.store(false);
    packet_counter_ = 0;
    capture_thread_ = std::thread(&PacketCapturer::capture_loop, this);

    return true;
}

void PacketCapturer::stop() {
    should_stop_.store(true);

    if (handle_) {
        // Romper el bucle de captura para evitar bloqueos infinitos de pcap_next_ex
        pcap_breakloop(handle_);
    }

    if (capture_thread_.joinable()) {
        capture_thread_.join();
    }

    if (handle_) {
        pcap_close(handle_);
        handle_ = nullptr;
    }

    if (session_) {
        session_->mark_stopped();
    }

    filter_.clear();
}

bool PacketCapturer::is_capturing() const {
    return session_ && session_->state() == CaptureState::Running;
}

// ══════════════════════════════════════════════════════════════
// Lectura de paquetes y estadísticas
// ══════════════════════════════════════════════════════════════

std::vector<PacketData> PacketCapturer::get_packets(std::size_t max_count) {
    if (!session_) return {};
    return session_->ring_buffer().pop_batch(max_count);
}

const CaptureStats& PacketCapturer::get_stats() const {
    static CaptureStats empty_stats;
    if (!session_) return empty_stats;
    return session_->stats();
}

std::string PacketCapturer::get_last_error() const {
    return last_error_;
}

// ══════════════════════════════════════════════════════════════
// Hilo de captura
// ══════════════════════════════════════════════════════════════

void PacketCapturer::capture_loop() {
    if (!handle_ || !session_) return;

    struct pcap_pkthdr* header = nullptr;
    const u_char*       data = nullptr;

    while (!should_stop_.load()) {
        int result = pcap_next_ex(handle_, &header, &data);

        switch (result) {
            case 1: {
                // Paquete capturado exitosamente
                PacketData packet;
                packet.number = ++packet_counter_;
                packet.timestamp = static_cast<double>(header->ts.tv_sec) +
                                   static_cast<double>(header->ts.tv_usec) / 1'000'000.0;
                packet.length = header->len;
                packet.captured_length = header->caplen;

                // Copiar datos raw
                packet.raw_data.assign(data, data + header->caplen);

                // Decodificar el paquete
                PacketDecoder::decode(data, header->caplen, packet);

                // Actualizar estadísticas
                session_->stats().record_packet(packet.protocol, header->len);

                // Insertar en el ring buffer
                if (!session_->ring_buffer().try_push(std::move(packet))) {
                    // Buffer lleno: incrementar contador de pérdidas
                    session_->stats().dropped_packets.fetch_add(1, std::memory_order_relaxed);
                }
                break;
            }
            case 0:
                // Timeout (sin paquetes), continuar
                break;

            case -1:
                // Error de pcap
                last_error_ = std::string("Error de captura: ") + pcap_geterr(handle_);
                session_->mark_error(last_error_);
                return;

            case -2:
                // EOF (leyendo de archivo)
                session_->mark_stopped();
                return;
        }

        // Actualizar rates periódicamente
        session_->stats().update_rates();
    }
}

} // namespace nexus
