/**
 * @file decoder.hpp
 * @brief Decodificador de paquetes de red (capas OSI).
 *
 * Procesa datos raw byte a byte para extraer cabeceras
 * Ethernet → IPv4 → TCP/UDP/ICMP/ARP. Alto rendimiento
 * con memcpy y ntohs/ntohl.
 */

#pragma once

#include "packet.hpp"
#include <cstdint>
#include <cstddef>

namespace nexus {

/**
 * @brief Decodificador estático de paquetes.
 *
 * Todos los métodos son estáticos y thread-safe (sin estado compartido).
 */
class PacketDecoder {
public:
    /**
     * @brief Decodifica un paquete raw completo desde la capa Ethernet.
     * @param data Puntero a los datos raw del paquete
     * @param length Longitud de los datos capturados
     * @param packet Estructura donde se almacenarán los datos decodificados
     * @return true si la decodificación fue exitosa (al menos Ethernet)
     */
    static bool decode(const uint8_t* data, std::size_t length, PacketData& packet);

private:
    /**
     * @brief Decodifica la cabecera Ethernet.
     * @return Offset al inicio de la carga útil (payload) de Ethernet
     */
    static std::size_t decode_ethernet(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Decodifica la cabecera IPv4.
     * @return Offset al inicio de la carga útil de IP
     */
    static std::size_t decode_ipv4(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Decodifica la cabecera TCP.
     */
    static void decode_tcp(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Decodifica la cabecera UDP.
     */
    static void decode_udp(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Decodifica la cabecera ICMP.
     */
    static void decode_icmp(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Decodifica la cabecera ARP.
     */
    static void decode_arp(const uint8_t* data, std::size_t length, PacketData& packet);

    /**
     * @brief Detecta el protocolo de aplicación basándose en puertos conocidos.
     */
    static ProtocolType detect_app_protocol(uint16_t src_port, uint16_t dst_port);

    /**
     * @brief Genera un resumen informativo del paquete.
     */
    static void build_info_string(PacketData& packet);
};

} // namespace nexus
