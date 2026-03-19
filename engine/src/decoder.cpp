/**
 * @file decoder.cpp
 * @brief Implementación del decodificador de paquetes de red.
 *
 * Decodifica paquetes raw byte a byte con memcpy + conversión de endianness.
 * Diseñado para rendimiento: ~miles de paquetes/seg sin asignaciones dinámicas extra.
 */

#include "nexus/decoder.hpp"
#include <cstring>  // memcpy
#include <sstream>

#ifdef _WIN32
    #include <winsock2.h>   // ntohs, ntohl
#else
    #include <arpa/inet.h>
#endif

namespace nexus {

// ══════════════════════════════════════════════════════════════
// Punto de entrada principal
// ══════════════════════════════════════════════════════════════

bool PacketDecoder::decode(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (!data || length < ETH_HEADER_SIZE) {
        return false;
    }

    // Paso 1: Ethernet
    std::size_t offset = decode_ethernet(data, length, packet);
    if (offset == 0) return false;

    // Paso 2: Capa de red
    switch (packet.ethernet.ethertype) {
        case ETHERTYPE_IPV4: {
            std::size_t ip_payload_offset = decode_ipv4(data + offset, length - offset, packet);
            if (ip_payload_offset > 0) {
                std::size_t transport_offset = offset + ip_payload_offset;
                std::size_t remaining = (transport_offset < length) ? length - transport_offset : 0;

                // Paso 3: Capa de transporte
                switch (packet.ipv4.protocol) {
                    case IP_PROTO_TCP:
                        decode_tcp(data + transport_offset, remaining, packet);
                        break;
                    case IP_PROTO_UDP:
                        decode_udp(data + transport_offset, remaining, packet);
                        break;
                    case IP_PROTO_ICMP:
                        decode_icmp(data + transport_offset, remaining, packet);
                        break;
                    default:
                        packet.protocol = ProtocolType::Unknown;
                        break;
                }
            }
            break;
        }
        case ETHERTYPE_ARP:
            decode_arp(data + offset, length - offset, packet);
            break;

        case ETHERTYPE_IPV6:
            packet.protocol = ProtocolType::IPv6;
            packet.has_ipv4 = false;
            break;

        default:
            packet.protocol = ProtocolType::Unknown;
            break;
    }

    // Paso 4: Construir string de información
    build_info_string(packet);

    return true;
}

// ══════════════════════════════════════════════════════════════
// Decodificadores por capa
// ══════════════════════════════════════════════════════════════

std::size_t PacketDecoder::decode_ethernet(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < ETH_HEADER_SIZE) return 0;

    // MAC destino (bytes 0-5)
    std::memcpy(packet.ethernet.dst_mac.data(), data, 6);
    // MAC origen (bytes 6-11)
    std::memcpy(packet.ethernet.src_mac.data(), data + 6, 6);
    // EtherType (bytes 12-13, big-endian)
    uint16_t raw_ethertype;
    std::memcpy(&raw_ethertype, data + 12, 2);
    packet.ethernet.ethertype = ntohs(raw_ethertype);

    packet.has_ethernet = true;
    packet.src_mac_str = mac_to_string(packet.ethernet.src_mac);
    packet.dst_mac_str = mac_to_string(packet.ethernet.dst_mac);

    // Manejar VLAN tagging (802.1Q)
    if (packet.ethernet.ethertype == ETHERTYPE_VLAN) {
        if (length < ETH_HEADER_SIZE + 4) return 0;
        std::memcpy(&raw_ethertype, data + 16, 2);
        packet.ethernet.ethertype = ntohs(raw_ethertype);
        return ETH_HEADER_SIZE + 4;  // 14 + 4 bytes de tag VLAN
    }

    return ETH_HEADER_SIZE;  // 14 bytes
}

std::size_t PacketDecoder::decode_ipv4(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < IPV4_HEADER_MIN_SIZE) return 0;

    // Versión + IHL (byte 0)
    uint8_t ver_ihl = data[0];
    packet.ipv4.version = (ver_ihl >> 4) & 0x0F;
    packet.ipv4.ihl = ver_ihl & 0x0F;

    if (packet.ipv4.version != 4) return 0;

    std::size_t header_size = static_cast<std::size_t>(packet.ipv4.ihl) * 4;
    if (header_size < IPV4_HEADER_MIN_SIZE || length < header_size) return 0;

    // DSCP + ECN (byte 1)
    packet.ipv4.dscp = (data[1] >> 2) & 0x3F;

    // Total Length (bytes 2-3)
    uint16_t raw_total;
    std::memcpy(&raw_total, data + 2, 2);
    packet.ipv4.total_length = ntohs(raw_total);

    // Identification (bytes 4-5)
    uint16_t raw_id;
    std::memcpy(&raw_id, data + 4, 2);
    packet.ipv4.identification = ntohs(raw_id);

    // Flags + Fragment Offset (bytes 6-7)
    uint16_t raw_flags_frag;
    std::memcpy(&raw_flags_frag, data + 6, 2);
    raw_flags_frag = ntohs(raw_flags_frag);
    packet.ipv4.flags = static_cast<uint8_t>((raw_flags_frag >> 13) & 0x07);
    packet.ipv4.fragment_offset = raw_flags_frag & 0x1FFF;

    // TTL (byte 8)
    packet.ipv4.ttl = data[8];

    // Protocol (byte 9)
    packet.ipv4.protocol = data[9];

    // Header Checksum (bytes 10-11)
    uint16_t raw_checksum;
    std::memcpy(&raw_checksum, data + 10, 2);
    packet.ipv4.checksum = ntohs(raw_checksum);

    // Source IP (bytes 12-15)
    std::memcpy(packet.ipv4.src_ip.data(), data + 12, 4);

    // Destination IP (bytes 16-19)
    std::memcpy(packet.ipv4.dst_ip.data(), data + 16, 4);

    packet.has_ipv4 = true;
    packet.src_ip_str = ipv4_to_string(packet.ipv4.src_ip);
    packet.dst_ip_str = ipv4_to_string(packet.ipv4.dst_ip);

    return header_size;
}

void PacketDecoder::decode_tcp(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < TCP_HEADER_MIN_SIZE) return;

    // Puerto origen (bytes 0-1)
    uint16_t raw_port;
    std::memcpy(&raw_port, data, 2);
    packet.tcp.src_port = ntohs(raw_port);

    // Puerto destino (bytes 2-3)
    std::memcpy(&raw_port, data + 2, 2);
    packet.tcp.dst_port = ntohs(raw_port);

    // Sequence Number (bytes 4-7)
    uint32_t raw_seq;
    std::memcpy(&raw_seq, data + 4, 4);
    packet.tcp.seq_number = ntohl(raw_seq);

    // Acknowledgment Number (bytes 8-11)
    uint32_t raw_ack;
    std::memcpy(&raw_ack, data + 8, 4);
    packet.tcp.ack_number = ntohl(raw_ack);

    // Data Offset + Flags (bytes 12-13)
    packet.tcp.data_offset = (data[12] >> 4) & 0x0F;
    packet.tcp.flags = data[13] & 0x3F;

    // Window Size (bytes 14-15)
    uint16_t raw_window;
    std::memcpy(&raw_window, data + 14, 2);
    packet.tcp.window_size = ntohs(raw_window);

    // Checksum (bytes 16-17)
    uint16_t raw_check;
    std::memcpy(&raw_check, data + 16, 2);
    packet.tcp.checksum = ntohs(raw_check);

    // Urgent Pointer (bytes 18-19)
    uint16_t raw_urg;
    std::memcpy(&raw_urg, data + 18, 2);
    packet.tcp.urgent_pointer = ntohs(raw_urg);

    packet.has_tcp = true;
    packet.src_port = packet.tcp.src_port;
    packet.dst_port = packet.tcp.dst_port;
    packet.protocol = detect_app_protocol(packet.tcp.src_port, packet.tcp.dst_port);

    // Si no se detectó protocolo de aplicación, etiquetar como TCP genérico
    if (packet.protocol == ProtocolType::Unknown) {
        packet.protocol = ProtocolType::TCP;
    }
}

void PacketDecoder::decode_udp(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < UDP_HEADER_SIZE) return;

    uint16_t raw_val;

    // Puerto origen (bytes 0-1)
    std::memcpy(&raw_val, data, 2);
    packet.udp.src_port = ntohs(raw_val);

    // Puerto destino (bytes 2-3)
    std::memcpy(&raw_val, data + 2, 2);
    packet.udp.dst_port = ntohs(raw_val);

    // Length (bytes 4-5)
    std::memcpy(&raw_val, data + 4, 2);
    packet.udp.length = ntohs(raw_val);

    // Checksum (bytes 6-7)
    std::memcpy(&raw_val, data + 6, 2);
    packet.udp.checksum = ntohs(raw_val);

    packet.has_udp = true;
    packet.src_port = packet.udp.src_port;
    packet.dst_port = packet.udp.dst_port;
    packet.protocol = detect_app_protocol(packet.udp.src_port, packet.udp.dst_port);

    if (packet.protocol == ProtocolType::Unknown) {
        packet.protocol = ProtocolType::UDP;
    }
}

void PacketDecoder::decode_icmp(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < ICMP_HEADER_MIN_SIZE) return;

    packet.icmp.type = data[0];
    packet.icmp.code = data[1];

    uint16_t raw_check;
    std::memcpy(&raw_check, data + 2, 2);
    packet.icmp.checksum = ntohs(raw_check);

    uint32_t raw_rest;
    std::memcpy(&raw_rest, data + 4, 4);
    packet.icmp.rest_of_header = ntohl(raw_rest);

    packet.has_icmp = true;
    packet.protocol = ProtocolType::ICMP;
}

void PacketDecoder::decode_arp(const uint8_t* data, std::size_t length, PacketData& packet) {
    if (length < ARP_HEADER_SIZE) return;

    uint16_t raw_val;

    // Hardware Type (bytes 0-1)
    std::memcpy(&raw_val, data, 2);
    packet.arp.hardware_type = ntohs(raw_val);

    // Protocol Type (bytes 2-3)
    std::memcpy(&raw_val, data + 2, 2);
    packet.arp.protocol_type = ntohs(raw_val);

    // Hardware Address Length (byte 4)
    packet.arp.hw_addr_len = data[4];

    // Protocol Address Length (byte 5)
    packet.arp.proto_addr_len = data[5];

    // Operation (bytes 6-7)
    std::memcpy(&raw_val, data + 6, 2);
    packet.arp.operation = ntohs(raw_val);

    // Sender MAC (bytes 8-13)
    std::memcpy(packet.arp.sender_mac.data(), data + 8, 6);

    // Sender IP (bytes 14-17)
    std::memcpy(packet.arp.sender_ip.data(), data + 14, 4);

    // Target MAC (bytes 18-23)
    std::memcpy(packet.arp.target_mac.data(), data + 18, 6);

    // Target IP (bytes 24-27)
    std::memcpy(packet.arp.target_ip.data(), data + 24, 4);

    packet.has_arp = true;
    packet.protocol = ProtocolType::ARP;

    // Para ARP, usar las IPs del ARP como src/dst
    packet.src_ip_str = ipv4_to_string(packet.arp.sender_ip);
    packet.dst_ip_str = ipv4_to_string(packet.arp.target_ip);
    packet.src_mac_str = mac_to_string(packet.arp.sender_mac);
    packet.dst_mac_str = mac_to_string(packet.arp.target_mac);
}

// ══════════════════════════════════════════════════════════════
// Detección de protocolo de aplicación
// ══════════════════════════════════════════════════════════════

ProtocolType PacketDecoder::detect_app_protocol(uint16_t src_port, uint16_t dst_port) {
    auto check = [&](uint16_t port) -> ProtocolType {
        switch (port) {
            case 53:   return ProtocolType::DNS;
            case 80:   return ProtocolType::HTTP;
            case 443:  return ProtocolType::HTTPS;
            case 22:   return ProtocolType::SSH;
            case 21:   return ProtocolType::FTP;
            case 25:
            case 587:  return ProtocolType::SMTP;
            case 67:
            case 68:   return ProtocolType::DHCP;
            case 161:
            case 162:  return ProtocolType::SNMP;
            case 23:   return ProtocolType::Telnet;
            default:   return ProtocolType::Unknown;
        }
    };

    ProtocolType proto = check(dst_port);
    if (proto != ProtocolType::Unknown) return proto;
    return check(src_port);
}

// ══════════════════════════════════════════════════════════════
// Generación del string informativo
// ══════════════════════════════════════════════════════════════

void PacketDecoder::build_info_string(PacketData& packet) {
    std::ostringstream oss;

    if (packet.has_arp) {
        oss << "ARP ";
        if (packet.arp.operation == 1) {
            oss << "Request: Who has " << packet.dst_ip_str
                << "? Tell " << packet.src_ip_str;
        } else if (packet.arp.operation == 2) {
            oss << "Reply: " << packet.src_ip_str
                << " is at " << packet.src_mac_str;
        }
    } else if (packet.has_tcp) {
        oss << packet.src_ip_str << ":" << packet.src_port
            << " → " << packet.dst_ip_str << ":" << packet.dst_port
            << " " << tcp_flags_to_string(packet.tcp.flags)
            << " Seq=" << packet.tcp.seq_number
            << " Win=" << packet.tcp.window_size
            << " Len=" << packet.length;
    } else if (packet.has_udp) {
        oss << packet.src_ip_str << ":" << packet.src_port
            << " → " << packet.dst_ip_str << ":" << packet.dst_port
            << " Len=" << packet.udp.length;
    } else if (packet.has_icmp) {
        oss << "ICMP Type=" << static_cast<int>(packet.icmp.type)
            << " Code=" << static_cast<int>(packet.icmp.code);
        if (packet.has_ipv4) {
            oss << " " << packet.src_ip_str << " → " << packet.dst_ip_str;
        }
    } else if (packet.protocol == ProtocolType::IPv6) {
        oss << "IPv6 " << packet.src_mac_str << " → " << packet.dst_mac_str;
    } else {
        oss << "Ethernet " << packet.src_mac_str << " → " << packet.dst_mac_str
            << " Type=0x" << std::hex << packet.ethernet.ethertype;
    }

    packet.info = oss.str();
}

} // namespace nexus
