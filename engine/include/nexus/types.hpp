/**
 * @file types.hpp
 * @brief Tipos fundamentales y constantes del motor NexusSniff.
 *
 * Define enumeraciones de protocolos, tipos auxiliares y constantes
 * de tamaño utilizadas en toda la capa de captura y decodificación.
 */

#pragma once

#include <cstdint>
#include <string>
#include <array>

namespace nexus {

// ══════════════════════════════════════════════════════════════
// Constantes de red
// ══════════════════════════════════════════════════════════════

/// Tamaño de cabecera Ethernet (bytes)
inline constexpr std::size_t ETH_HEADER_SIZE = 14;

/// Tamaño mínimo de cabecera IPv4 (bytes, sin opciones)
inline constexpr std::size_t IPV4_HEADER_MIN_SIZE = 20;

/// Tamaño de cabecera TCP mínima (bytes, sin opciones)
inline constexpr std::size_t TCP_HEADER_MIN_SIZE = 20;

/// Tamaño de cabecera UDP (bytes)
inline constexpr std::size_t UDP_HEADER_SIZE = 8;

/// Tamaño de cabecera ICMP mínima (bytes)
inline constexpr std::size_t ICMP_HEADER_MIN_SIZE = 8;

/// Tamaño de cabecera ARP (bytes)
inline constexpr std::size_t ARP_HEADER_SIZE = 28;

/// Tamaño del ring buffer por defecto (paquetes)
inline constexpr std::size_t DEFAULT_RING_BUFFER_SIZE = 65536;

/// Snapshot length por defecto (bytes capturados por paquete)
inline constexpr int DEFAULT_SNAP_LEN = 65535;

/// Timeout de lectura de paquetes (ms)
inline constexpr int DEFAULT_READ_TIMEOUT_MS = 100;

// ══════════════════════════════════════════════════════════════
// EtherTypes (IEEE 802.3)
// ══════════════════════════════════════════════════════════════

inline constexpr uint16_t ETHERTYPE_IPV4 = 0x0800;
inline constexpr uint16_t ETHERTYPE_ARP  = 0x0806;
inline constexpr uint16_t ETHERTYPE_IPV6 = 0x86DD;
inline constexpr uint16_t ETHERTYPE_VLAN = 0x8100;

// ══════════════════════════════════════════════════════════════
// Números de protocolo IP (IANA)
// ══════════════════════════════════════════════════════════════

inline constexpr uint8_t IP_PROTO_ICMP = 1;
inline constexpr uint8_t IP_PROTO_TCP  = 6;
inline constexpr uint8_t IP_PROTO_UDP  = 17;
inline constexpr uint8_t IP_PROTO_ICMPV6 = 58;

// ══════════════════════════════════════════════════════════════
// Enumeraciones
// ══════════════════════════════════════════════════════════════

/// Tipo de protocolo de capa de aplicación detectado.
enum class ProtocolType : uint8_t {
    Unknown = 0,
    ARP,
    ICMP,
    TCP,
    UDP,
    DNS,
    HTTP,
    HTTPS,
    SSH,
    FTP,
    SMTP,
    DHCP,
    SNMP,
    Telnet,
    ICMPv6,
    IPv6
};

/// Estado de una sesión de captura.
enum class CaptureState : uint8_t {
    Idle = 0,     ///< Sin captura activa
    Running,      ///< Capturando paquetes
    Paused,       ///< Pausada temporalmente
    Stopped,      ///< Finalizada por el usuario
    Error         ///< Error en la captura
};

// ══════════════════════════════════════════════════════════════
// Tipos auxiliares
// ══════════════════════════════════════════════════════════════

/// Dirección MAC (6 bytes).
using MacAddress = std::array<uint8_t, 6>;

/// Dirección IPv4 (4 bytes).
using IPv4Address = std::array<uint8_t, 4>;

/// Dirección IPv6 (16 bytes).
using IPv6Address = std::array<uint8_t, 16>;

// ══════════════════════════════════════════════════════════════
// Utilidades
// ══════════════════════════════════════════════════════════════

/**
 * @brief Convierte una MacAddress a su representación string "AA:BB:CC:DD:EE:FF".
 */
[[nodiscard]] inline std::string mac_to_string(const MacAddress& mac) {
    char buf[18];
    std::snprintf(buf, sizeof(buf), "%02x:%02x:%02x:%02x:%02x:%02x",
                  mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    return std::string(buf);
}

/**
 * @brief Convierte una IPv4Address a su representación string "A.B.C.D".
 */
[[nodiscard]] inline std::string ipv4_to_string(const IPv4Address& ip) {
    char buf[16];
    std::snprintf(buf, sizeof(buf), "%u.%u.%u.%u", ip[0], ip[1], ip[2], ip[3]);
    return std::string(buf);
}

/**
 * @brief Devuelve el nombre legible de un ProtocolType.
 */
[[nodiscard]] inline std::string protocol_to_string(ProtocolType proto) {
    switch (proto) {
        case ProtocolType::ARP:    return "ARP";
        case ProtocolType::ICMP:   return "ICMP";
        case ProtocolType::TCP:    return "TCP";
        case ProtocolType::UDP:    return "UDP";
        case ProtocolType::DNS:    return "DNS";
        case ProtocolType::HTTP:   return "HTTP";
        case ProtocolType::HTTPS:  return "HTTPS";
        case ProtocolType::SSH:    return "SSH";
        case ProtocolType::FTP:    return "FTP";
        case ProtocolType::SMTP:   return "SMTP";
        case ProtocolType::DHCP:   return "DHCP";
        case ProtocolType::SNMP:   return "SNMP";
        case ProtocolType::Telnet: return "Telnet";
        case ProtocolType::ICMPv6: return "ICMPv6";
        case ProtocolType::IPv6:   return "IPv6";
        default:                   return "Unknown";
    }
}

} // namespace nexus
