/**
 * @file filter.hpp
 * @brief Wrapper para filtros BPF (Berkeley Packet Filter).
 *
 * Encapsula la compilación y aplicación de filtros BPF
 * sobre un handle pcap activo.
 */

#pragma once

#include <string>
#include <pcap.h>

namespace nexus {

/**
 * @brief Gestor de filtros BPF para captura de paquetes.
 */
class BpfFilter {
public:
    BpfFilter() = default;
    ~BpfFilter();

    // No copiable
    BpfFilter(const BpfFilter&) = delete;
    BpfFilter& operator=(const BpfFilter&) = delete;

    // Movible
    BpfFilter(BpfFilter&& other) noexcept;
    BpfFilter& operator=(BpfFilter&& other) noexcept;

    /**
     * @brief Compila y aplica un filtro BPF al handle pcap.
     * @param handle Handle pcap activo
     * @param expression Expresión BPF (ej: "tcp port 80")
     * @param netmask Máscara de red (0 si no se conoce)
     * @return true si el filtro fue compilado y aplicado exitosamente
     */
    bool apply(pcap_t* handle, const std::string& expression, uint32_t netmask = 0);

    /**
     * @brief Valida una expresión BPF sin aplicarla.
     * @param expression Expresión BPF a validar
     * @return true si la expresión es sintácticamente válida
     */
    static bool validate(const std::string& expression);

    /**
     * @brief Devuelve el último error ocurrido.
     */
    [[nodiscard]] const std::string& last_error() const { return last_error_; }

    /**
     * @brief Devuelve la expresión BPF actualmente aplicada.
     */
    [[nodiscard]] const std::string& expression() const { return expression_; }

    /**
     * @brief Indica si hay un filtro activo.
     */
    [[nodiscard]] bool is_active() const { return compiled_; }

    /**
     * @brief Limpia el filtro compilado.
     */
    void clear();

private:
    struct bpf_program program_{};
    bool               compiled_ = false;
    std::string        expression_;
    std::string        last_error_;
};

} // namespace nexus
