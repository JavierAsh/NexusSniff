/**
 * @file packet.cpp
 * @brief Implementación de utilidades de PacketData.
 */

#include "nexus/packet.hpp"
#include <sstream>

namespace nexus {

std::string tcp_flags_to_string(uint8_t flags) {
    std::string result = "[";
    bool first = true;

    auto append_flag = [&](uint8_t mask, const char* name) {
        if (flags & mask) {
            if (!first) result += ", ";
            result += name;
            first = false;
        }
    };

    append_flag(TCP_FLAG_SYN, "SYN");
    append_flag(TCP_FLAG_ACK, "ACK");
    append_flag(TCP_FLAG_FIN, "FIN");
    append_flag(TCP_FLAG_RST, "RST");
    append_flag(TCP_FLAG_PSH, "PSH");
    append_flag(TCP_FLAG_URG, "URG");

    result += "]";
    return result;
}

} // namespace nexus
