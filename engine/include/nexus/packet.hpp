/**
 * @file packet.hpp
 * @brief Estructura de paquete de red decodificado.
 *
 * Contiene PacketData: representación completa de un paquete capturado
 * con todas las capas decodificadas y los datos raw.
 */

#pragma once

#include "types.hpp"
#include <vector>
#include <string>
#include <chrono>
#include <cstdint>

namespace nexus {

/**
 * @brief Información de la capa Ethernet decodificada.
 */
struct EthernetLayer {
    MacAddress src_mac{};
    MacAddress dst_mac{};
    uint16_t   ethertype = 0;
};

/**
 * @brief Información de la capa IPv4 decodificada.
 */
struct IPv4Layer {
    uint8_t     version = 4;
    uint8_t     ihl = 5;            ///< Internet Header Length (palabras de 32 bits)
    uint8_t     dscp = 0;           ///< Differentiated Services Code Point
    uint16_t    total_length = 0;
    uint16_t    identification = 0;
    uint8_t     flags = 0;
    uint16_t    fragment_offset = 0;
    uint8_t     ttl = 0;
    uint8_t     protocol = 0;       ///< Número de protocolo (TCP=6, UDP=17, etc.)
    uint16_t    checksum = 0;
    IPv4Address src_ip{};
    IPv4Address dst_ip{};
};

/**
 * @brief Información de la capa TCP decodificada.
 */
struct TcpLayer {
    uint16_t src_port = 0;
    uint16_t dst_port = 0;
    uint32_t seq_number = 0;
    uint32_t ack_number = 0;
    uint8_t  data_offset = 5;   ///< Tamaño de cabecera TCP en palabras de 32 bits
    uint8_t  flags = 0;         ///< SYN, ACK, FIN, RST, PSH, URG
    uint16_t window_size = 0;
    uint16_t checksum = 0;
    uint16_t urgent_pointer = 0;
};

// Máscaras para flags TCP
inline constexpr uint8_t TCP_FLAG_FIN = 0x01;
inline constexpr uint8_t TCP_FLAG_SYN = 0x02;
inline constexpr uint8_t TCP_FLAG_RST = 0x04;
inline constexpr uint8_t TCP_FLAG_PSH = 0x08;
inline constexpr uint8_t TCP_FLAG_ACK = 0x10;
inline constexpr uint8_t TCP_FLAG_URG = 0x20;

/**
 * @brief Información de la capa UDP decodificada.
 */
struct UdpLayer {
    uint16_t src_port = 0;
    uint16_t dst_port = 0;
    uint16_t length = 0;
    uint16_t checksum = 0;
};

/**
 * @brief Información de la capa ICMP decodificada.
 */
struct IcmpLayer {
    uint8_t  type = 0;
    uint8_t  code = 0;
    uint16_t checksum = 0;
    uint32_t rest_of_header = 0;  ///< Varía según el tipo ICMP
};

/**
 * @brief Información de la capa ARP decodificada.
 */
struct ArpLayer {
    uint16_t   hardware_type = 0;
    uint16_t   protocol_type = 0;
    uint8_t    hw_addr_len = 0;
    uint8_t    proto_addr_len = 0;
    uint16_t   operation = 0;       ///< 1 = Request, 2 = Reply
    MacAddress sender_mac{};
    IPv4Address sender_ip{};
    MacAddress target_mac{};
    IPv4Address target_ip{};
};

/**
 * @brief Representación completa de un paquete de red capturado y decodificado.
 *
 * Gestión segura de memoria: usa std::vector para datos raw,
 * y structs por valor para las capas (sin new/delete).
 */
struct PacketData {
    /// Número secuencial del paquete en la sesión
    uint64_t number = 0;

    /// Timestamp de captura (microsegundos desde epoch)
    double timestamp = 0.0;

    /// Longitud total del paquete (bytes en el cable)
    uint32_t length = 0;

    /// Longitud capturada (puede ser menor que length si snap_len < longitud real)
    uint32_t captured_length = 0;

    // ── Capas decodificadas ──
    EthernetLayer ethernet;
    IPv4Layer     ipv4;
    TcpLayer      tcp;
    UdpLayer      udp;
    IcmpLayer     icmp;
    ArpLayer      arp;

    /// Protocolo de alto nivel detectado
    ProtocolType protocol = ProtocolType::Unknown;

    /// Descripción resumida del paquete (ej: "TCP 192.168.1.1:443 → 10.0.0.5:52341 [ACK]")
    std::string info;

    /// IP origen como string
    std::string src_ip_str;

    /// IP destino como string
    std::string dst_ip_str;

    /// MAC origen como string
    std::string src_mac_str;

    /// MAC destino como string
    std::string dst_mac_str;

    /// Puerto origen (0 si no aplica)
    uint16_t src_port = 0;

    /// Puerto destino (0 si no aplica)
    uint16_t dst_port = 0;

    /// Datos raw del paquete capturado
    std::vector<uint8_t> raw_data;

    /// Flags legibles (ej: {"SYN", "ACK"})
    bool has_ethernet = false;
    bool has_ipv4     = false;
    bool has_tcp      = false;
    bool has_udp      = false;
    bool has_icmp     = false;
    bool has_arp      = false;
};

/**
 * @brief Devuelve string con los flags TCP activos.
 * @param flags Byte de flags TCP
 * @return String como "[SYN, ACK]"
 */
[[nodiscard]] std::string tcp_flags_to_string(uint8_t flags);

} // namespace nexus
