/**
 * @file session.cpp
 * @brief Implementación del ring buffer y sesión de captura.
 */

#include "nexus/session.hpp"
#include <algorithm>

namespace nexus {

// ══════════════════════════════════════════════════════════════
// PacketRingBuffer
// ══════════════════════════════════════════════════════════════

PacketRingBuffer::PacketRingBuffer(std::size_t capacity)
    : buffer_(capacity)
    , capacity_(capacity)
{
}

bool PacketRingBuffer::try_push(PacketData&& packet) {
    std::size_t current_head = head_.load(std::memory_order_relaxed);
    std::size_t next_head = (current_head + 1) % capacity_;

    // Buffer lleno si el siguiente head alcanza al tail
    if (next_head == tail_.load(std::memory_order_acquire)) {
        return false;
    }

    buffer_[current_head] = std::move(packet);
    head_.store(next_head, std::memory_order_release);
    return true;
}

std::optional<PacketData> PacketRingBuffer::try_pop() {
    std::size_t current_tail = tail_.load(std::memory_order_relaxed);

    // Buffer vacío si tail == head
    if (current_tail == head_.load(std::memory_order_acquire)) {
        return std::nullopt;
    }

    PacketData packet = std::move(buffer_[current_tail]);
    tail_.store((current_tail + 1) % capacity_, std::memory_order_release);
    return packet;
}

std::vector<PacketData> PacketRingBuffer::pop_batch(std::size_t max_count) {
    std::vector<PacketData> result;
    result.reserve(std::min(max_count, size()));

    for (std::size_t i = 0; i < max_count; ++i) {
        auto packet = try_pop();
        if (!packet.has_value()) break;
        result.push_back(std::move(*packet));
    }

    return result;
}

std::size_t PacketRingBuffer::size() const {
    std::size_t h = head_.load(std::memory_order_acquire);
    std::size_t t = tail_.load(std::memory_order_acquire);

    if (h >= t) {
        return h - t;
    }
    return capacity_ - t + h;
}

void PacketRingBuffer::clear() {
    head_.store(0, std::memory_order_release);
    tail_.store(0, std::memory_order_release);
}

// ══════════════════════════════════════════════════════════════
// CaptureSession
// ══════════════════════════════════════════════════════════════

CaptureSession::CaptureSession(
    std::string name,
    std::string interface_name,
    std::string bpf_filter,
    std::size_t buffer_size
)
    : name_(std::move(name))
    , interface_name_(std::move(interface_name))
    , bpf_filter_(std::move(bpf_filter))
    , ring_buffer_(buffer_size)
{
}

void CaptureSession::mark_started() {
    state_.store(CaptureState::Running);
    start_time_ = std::chrono::steady_clock::now();
    stats_.reset();
}

void CaptureSession::mark_stopped() {
    state_.store(CaptureState::Stopped);
    end_time_ = std::chrono::steady_clock::now();
}

void CaptureSession::mark_error(const std::string& error_msg) {
    last_error_ = error_msg;
    state_.store(CaptureState::Error);
    end_time_ = std::chrono::steady_clock::now();
}

double CaptureSession::duration_seconds() const {
    auto end = (state_.load() == CaptureState::Running)
        ? std::chrono::steady_clock::now()
        : end_time_;

    return std::chrono::duration<double>(end - start_time_).count();
}

} // namespace nexus
