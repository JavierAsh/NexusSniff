/**
 * @file filter.cpp
 * @brief Implementación del wrapper de filtros BPF.
 */

#include "nexus/filter.hpp"

namespace nexus {

BpfFilter::~BpfFilter() {
    clear();
}

BpfFilter::BpfFilter(BpfFilter&& other) noexcept
    : program_(other.program_)
    , compiled_(other.compiled_)
    , expression_(std::move(other.expression_))
    , last_error_(std::move(other.last_error_))
{
    other.compiled_ = false;
}

BpfFilter& BpfFilter::operator=(BpfFilter&& other) noexcept {
    if (this != &other) {
        clear();
        program_ = other.program_;
        compiled_ = other.compiled_;
        expression_ = std::move(other.expression_);
        last_error_ = std::move(other.last_error_);
        other.compiled_ = false;
    }
    return *this;
}

bool BpfFilter::apply(pcap_t* handle, const std::string& expression, uint32_t netmask) {
    if (!handle) {
        last_error_ = "Handle pcap nulo";
        return false;
    }

    // Limpiar filtro anterior si existe
    clear();

    // Compilar la expresión BPF
    if (pcap_compile(handle, &program_, expression.c_str(),
                     1 /* optimizar */, netmask) == -1) {
        last_error_ = std::string("Error compilando filtro BPF: ") + pcap_geterr(handle);
        return false;
    }

    compiled_ = true;

    // Aplicar el filtro compilado al handle
    if (pcap_setfilter(handle, &program_) == -1) {
        last_error_ = std::string("Error aplicando filtro BPF: ") + pcap_geterr(handle);
        clear();
        return false;
    }

    expression_ = expression;
    return true;
}

bool BpfFilter::validate(const std::string& expression) {
    // Crear un handle temporal solo para validar la sintaxis
    pcap_t* temp_handle = pcap_open_dead(DLT_EN10MB, 65535);
    if (!temp_handle) return false;

    struct bpf_program temp_prog{};
    bool valid = (pcap_compile(temp_handle, &temp_prog, expression.c_str(),
                               1, 0) == 0);

    if (valid) {
        pcap_freecode(&temp_prog);
    }

    pcap_close(temp_handle);
    return valid;
}

void BpfFilter::clear() {
    if (compiled_) {
        pcap_freecode(&program_);
        compiled_ = false;
    }
    expression_.clear();
}

} // namespace nexus
