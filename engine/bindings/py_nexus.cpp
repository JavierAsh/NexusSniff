/**
 * @file py_nexus.cpp
 * @brief Bindings pybind11 para el motor de captura NexusSniff.
 *
 * Expone las clases y funciones del motor C++ como módulo Python
 * 'nexus_engine' importable directamente.
 *
 * GIL se libera durante operaciones de captura para no bloquear Python.
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>

#include "nexus/capturer.hpp"
#include "nexus/packet.hpp"
#include "nexus/types.hpp"
#include "nexus/stats.hpp"
#include "nexus/filter.hpp"

namespace py = pybind11;

PYBIND11_MODULE(nexus_engine, m) {
    m.doc() = "NexusSniff — Motor de captura de paquetes de red de alto rendimiento";

    // ══════════════════════════════════════════════════════════════
    // Enumeraciones
    // ══════════════════════════════════════════════════════════════

    py::enum_<nexus::ProtocolType>(m, "ProtocolType")
        .value("Unknown", nexus::ProtocolType::Unknown)
        .value("ARP",     nexus::ProtocolType::ARP)
        .value("ICMP",    nexus::ProtocolType::ICMP)
        .value("TCP",     nexus::ProtocolType::TCP)
        .value("UDP",     nexus::ProtocolType::UDP)
        .value("DNS",     nexus::ProtocolType::DNS)
        .value("HTTP",    nexus::ProtocolType::HTTP)
        .value("HTTPS",   nexus::ProtocolType::HTTPS)
        .value("SSH",     nexus::ProtocolType::SSH)
        .value("FTP",     nexus::ProtocolType::FTP)
        .value("SMTP",    nexus::ProtocolType::SMTP)
        .value("DHCP",    nexus::ProtocolType::DHCP)
        .value("SNMP",    nexus::ProtocolType::SNMP)
        .value("Telnet",  nexus::ProtocolType::Telnet)
        .value("ICMPv6",  nexus::ProtocolType::ICMPv6)
        .value("IPv6",    nexus::ProtocolType::IPv6)
        .export_values();

    py::enum_<nexus::CaptureState>(m, "CaptureState")
        .value("Idle",    nexus::CaptureState::Idle)
        .value("Running", nexus::CaptureState::Running)
        .value("Paused",  nexus::CaptureState::Paused)
        .value("Stopped", nexus::CaptureState::Stopped)
        .value("Error",   nexus::CaptureState::Error)
        .export_values();

    // ══════════════════════════════════════════════════════════════
    // Estructuras de capas
    // ══════════════════════════════════════════════════════════════

    py::class_<nexus::EthernetLayer>(m, "EthernetLayer")
        .def_readonly("ethertype", &nexus::EthernetLayer::ethertype);

    py::class_<nexus::IPv4Layer>(m, "IPv4Layer")
        .def_readonly("version",        &nexus::IPv4Layer::version)
        .def_readonly("ihl",            &nexus::IPv4Layer::ihl)
        .def_readonly("total_length",   &nexus::IPv4Layer::total_length)
        .def_readonly("identification", &nexus::IPv4Layer::identification)
        .def_readonly("ttl",            &nexus::IPv4Layer::ttl)
        .def_readonly("protocol",       &nexus::IPv4Layer::protocol)
        .def_readonly("checksum",       &nexus::IPv4Layer::checksum);

    py::class_<nexus::TcpLayer>(m, "TcpLayer")
        .def_readonly("src_port",      &nexus::TcpLayer::src_port)
        .def_readonly("dst_port",      &nexus::TcpLayer::dst_port)
        .def_readonly("seq_number",    &nexus::TcpLayer::seq_number)
        .def_readonly("ack_number",    &nexus::TcpLayer::ack_number)
        .def_readonly("flags",         &nexus::TcpLayer::flags)
        .def_readonly("window_size",   &nexus::TcpLayer::window_size)
        .def_readonly("checksum",      &nexus::TcpLayer::checksum);

    py::class_<nexus::UdpLayer>(m, "UdpLayer")
        .def_readonly("src_port", &nexus::UdpLayer::src_port)
        .def_readonly("dst_port", &nexus::UdpLayer::dst_port)
        .def_readonly("length",   &nexus::UdpLayer::length)
        .def_readonly("checksum", &nexus::UdpLayer::checksum);

    py::class_<nexus::IcmpLayer>(m, "IcmpLayer")
        .def_readonly("type",     &nexus::IcmpLayer::type)
        .def_readonly("code",     &nexus::IcmpLayer::code)
        .def_readonly("checksum", &nexus::IcmpLayer::checksum);

    py::class_<nexus::ArpLayer>(m, "ArpLayer")
        .def_readonly("hardware_type",  &nexus::ArpLayer::hardware_type)
        .def_readonly("protocol_type",  &nexus::ArpLayer::protocol_type)
        .def_readonly("operation",      &nexus::ArpLayer::operation);

    // ══════════════════════════════════════════════════════════════
    // PacketData
    // ══════════════════════════════════════════════════════════════

    py::class_<nexus::PacketData>(m, "PacketData")
        .def_readonly("number",          &nexus::PacketData::number)
        .def_readonly("timestamp",       &nexus::PacketData::timestamp)
        .def_readonly("length",          &nexus::PacketData::length)
        .def_readonly("captured_length", &nexus::PacketData::captured_length)
        .def_readonly("protocol",        &nexus::PacketData::protocol)
        .def_readonly("info",            &nexus::PacketData::info)
        .def_readonly("src_ip_str",      &nexus::PacketData::src_ip_str)
        .def_readonly("dst_ip_str",      &nexus::PacketData::dst_ip_str)
        .def_readonly("src_mac_str",     &nexus::PacketData::src_mac_str)
        .def_readonly("dst_mac_str",     &nexus::PacketData::dst_mac_str)
        .def_readonly("src_port",        &nexus::PacketData::src_port)
        .def_readonly("dst_port",        &nexus::PacketData::dst_port)
        .def_readonly("raw_data",        &nexus::PacketData::raw_data)
        .def_readonly("has_ethernet",    &nexus::PacketData::has_ethernet)
        .def_readonly("has_ipv4",        &nexus::PacketData::has_ipv4)
        .def_readonly("has_tcp",         &nexus::PacketData::has_tcp)
        .def_readonly("has_udp",         &nexus::PacketData::has_udp)
        .def_readonly("has_icmp",        &nexus::PacketData::has_icmp)
        .def_readonly("has_arp",         &nexus::PacketData::has_arp)
        // Acceso a sub-capas
        .def_readonly("ethernet",        &nexus::PacketData::ethernet)
        .def_readonly("ipv4",            &nexus::PacketData::ipv4)
        .def_readonly("tcp",             &nexus::PacketData::tcp)
        .def_readonly("udp",             &nexus::PacketData::udp)
        .def_readonly("icmp",            &nexus::PacketData::icmp)
        .def_readonly("arp",             &nexus::PacketData::arp)
        // Nombre del protocolo como string
        .def_property_readonly("protocol_name", [](const nexus::PacketData& p) {
            return nexus::protocol_to_string(p.protocol);
        })
        .def("__repr__", [](const nexus::PacketData& p) {
            return "<PacketData #" + std::to_string(p.number)
                   + " " + nexus::protocol_to_string(p.protocol)
                   + " " + p.src_ip_str + " -> " + p.dst_ip_str + ">";
        });

    // ══════════════════════════════════════════════════════════════
    // NetworkInterface
    // ══════════════════════════════════════════════════════════════

    py::class_<nexus::NetworkInterface>(m, "NetworkInterface")
        .def_readonly("name",        &nexus::NetworkInterface::name)
        .def_readonly("description", &nexus::NetworkInterface::description)
        .def_readonly("addresses",   &nexus::NetworkInterface::addresses)
        .def_readonly("is_loopback", &nexus::NetworkInterface::is_loopback)
        .def("__repr__", [](const nexus::NetworkInterface& iface) {
            return "<NetworkInterface '" + iface.description + "' " + iface.name + ">";
        });

    // ══════════════════════════════════════════════════════════════
    // CaptureStats
    // ══════════════════════════════════════════════════════════════

    py::class_<nexus::CaptureStats>(m, "CaptureStats")
        .def_property_readonly("total_packets", [](const nexus::CaptureStats& s) {
            return s.total_packets.load();
        })
        .def_property_readonly("total_bytes", [](const nexus::CaptureStats& s) {
            return s.total_bytes.load();
        })
        .def_property_readonly("dropped_packets", [](const nexus::CaptureStats& s) {
            return s.dropped_packets.load();
        })
        .def_property_readonly("packets_per_sec", [](const nexus::CaptureStats& s) {
            return s.packets_per_sec.load();
        })
        .def_property_readonly("bytes_per_sec", [](const nexus::CaptureStats& s) {
            return s.bytes_per_sec.load();
        })
        .def("get_protocol_distribution", &nexus::CaptureStats::get_protocol_distribution);

    // ══════════════════════════════════════════════════════════════
    // PacketCapturer
    // ══════════════════════════════════════════════════════════════

    py::class_<nexus::PacketCapturer>(m, "PacketCapturer")
        .def(py::init<>())
        .def_static("list_interfaces", &nexus::PacketCapturer::list_interfaces,
            "Enumera todas las interfaces de red disponibles.")
        .def("start", &nexus::PacketCapturer::start,
            py::call_guard<py::gil_scoped_release>(),
            py::arg("interface_name"),
            py::arg("bpf_filter") = "",
            py::arg("snap_len") = nexus::DEFAULT_SNAP_LEN,
            py::arg("buffer_size") = nexus::DEFAULT_RING_BUFFER_SIZE,
            "Inicia la captura en la interfaz especificada.")
        .def("stop", &nexus::PacketCapturer::stop,
            py::call_guard<py::gil_scoped_release>(),
            "Detiene la captura activa.")
        .def("is_capturing", &nexus::PacketCapturer::is_capturing,
            "Indica si hay una captura en curso.")
        .def("get_packets", &nexus::PacketCapturer::get_packets,
            py::arg("max_count") = 256,
            "Obtiene hasta N paquetes del ring buffer.")
        .def("get_stats", &nexus::PacketCapturer::get_stats,
            py::return_value_policy::reference_internal,
            "Obtiene las estadísticas de captura actuales.")
        .def("get_last_error", &nexus::PacketCapturer::get_last_error,
            "Obtiene el último error ocurrido.");

    // ══════════════════════════════════════════════════════════════
    // Funciones de utilidad
    // ══════════════════════════════════════════════════════════════

    m.def("validate_bpf_filter", &nexus::BpfFilter::validate,
        py::arg("expression"),
        "Valida una expresión BPF sin aplicarla.");

    m.def("protocol_to_string", &nexus::protocol_to_string,
        py::arg("protocol"),
        "Convierte un ProtocolType a su nombre legible.");

    m.def("tcp_flags_to_string", &nexus::tcp_flags_to_string,
        py::arg("flags"),
        "Convierte flags TCP (byte) a representación string.");
}
