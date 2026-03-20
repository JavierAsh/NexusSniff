/**
 * @file test_ring_buffer.cpp
 * @brief Tests unitarios para el ring buffer SPSC y CaptureStats lock-free.
 *
 * Usa Catch2 (header-only) para validar la concurrencia y corrección
 * del ring buffer y el sistema de estadísticas.
 */

#define CATCH_CONFIG_MAIN
#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include "nexus/session.hpp"
#include "nexus/stats.hpp"
#include "nexus/types.hpp"

#include <thread>
#include <vector>
#include <atomic>

using namespace nexus;

// ══════════════════════════════════════════════════════════════
// Tests del Ring Buffer SPSC
// ══════════════════════════════════════════════════════════════

TEST_CASE("Ring buffer: operaciones básicas", "[ringbuffer]") {
    PacketRingBuffer buffer(64);

    SECTION("Buffer recién creado está vacío") {
        REQUIRE(buffer.size() == 0);
        REQUIRE(buffer.empty());
    }

    SECTION("Push y pop de un elemento") {
        PacketData pkt;
        pkt.number = 1;
        pkt.length = 100;
        pkt.protocol = ProtocolType::TCP;

        bool pushed = buffer.try_push(std::move(pkt));
        REQUIRE(pushed);
        REQUIRE(buffer.size() == 1);

        auto out_opt = buffer.try_pop();
        bool popped = out_opt.has_value();
        REQUIRE(popped);
        REQUIRE(out_opt->number == 1);
        REQUIRE(out_opt->length == 100);
        REQUIRE(buffer.empty());
    }

    SECTION("Pop de buffer vacío falla") {
        auto out_opt = buffer.try_pop();
        bool popped = out_opt.has_value();
        REQUIRE_FALSE(popped);
    }

    SECTION("Push hasta llenar el buffer") {
        PacketRingBuffer small_buf(4);

        for (uint32_t i = 0; i < 3; ++i) {
            PacketData pkt;
            pkt.number = i;
            REQUIRE(small_buf.try_push(std::move(pkt)));
        }
        // Buffer lleno (capacity - 1 elementos en SPSC)
        PacketData overflow_pkt;
        overflow_pkt.number = 999;
        bool pushed = small_buf.try_push(std::move(overflow_pkt));
        REQUIRE_FALSE(pushed);
    }
}

TEST_CASE("Ring buffer: batch pop", "[ringbuffer]") {
    PacketRingBuffer buffer(128);

    // Insertar 50 paquetes
    for (uint32_t i = 0; i < 50; ++i) {
        PacketData pkt;
        pkt.number = i;
        pkt.protocol = ProtocolType::TCP;
        buffer.try_push(std::move(pkt));
    }

    SECTION("Pop de batch parcial") {
        auto batch = buffer.pop_batch(20);
        REQUIRE(batch.size() == 20);
        REQUIRE(batch[0].number == 0);
        REQUIRE(batch[19].number == 19);
        REQUIRE(buffer.size() == 30);
    }

    SECTION("Pop de todo") {
        auto batch = buffer.pop_batch(100);
        REQUIRE(batch.size() == 50);
        REQUIRE(buffer.empty());
    }
}

TEST_CASE("Ring buffer: concurrencia SPSC", "[ringbuffer][threading]") {
    PacketRingBuffer buffer(4096);
    const int NUM_PACKETS = 10000;
    std::atomic<int> produced{0};
    std::atomic<int> consumed{0};

    // Productor: inserta NUM_PACKETS
    std::thread producer([&] {
        for (int i = 0; i < NUM_PACKETS; ++i) {
            PacketData pkt;
            pkt.number = static_cast<uint32_t>(i);
            pkt.length = 64;
            while (!buffer.try_push(std::move(pkt))) {
                std::this_thread::yield();
                pkt.number = static_cast<uint32_t>(i); // Restore pkt content for retry
                pkt.length = 64;
            }
            produced.fetch_add(1);
        }
    });

    // Consumidor: drena hasta NUM_PACKETS
    std::thread consumer([&] {
        int count = 0;
        while (count < NUM_PACKETS) {
            auto batch = buffer.pop_batch(256);
            count += static_cast<int>(batch.size());
            consumed.store(count);
            if (batch.empty()) {
                std::this_thread::yield();
            }
        }
    });

    producer.join();
    consumer.join();

    REQUIRE(produced.load() == NUM_PACKETS);
    REQUIRE(consumed.load() == NUM_PACKETS);
    REQUIRE(buffer.empty());
}

// ══════════════════════════════════════════════════════════════
// Tests de CaptureStats (lock-free)
// ══════════════════════════════════════════════════════════════

TEST_CASE("CaptureStats: contadores básicos", "[stats]") {
    CaptureStats stats;

    SECTION("Contadores inician en 0") {
        REQUIRE(stats.total_packets.load() == 0);
        REQUIRE(stats.total_bytes.load() == 0);
        REQUIRE(stats.dropped_packets.load() == 0);
    }

    SECTION("record_packet incrementa contadores") {
        stats.record_packet(ProtocolType::TCP, 100);
        stats.record_packet(ProtocolType::TCP, 200);
        stats.record_packet(ProtocolType::UDP, 50);

        REQUIRE(stats.total_packets.load() == 3);
        REQUIRE(stats.total_bytes.load() == 350);
    }

    SECTION("Distribución de protocolos") {
        stats.record_packet(ProtocolType::TCP, 100);
        stats.record_packet(ProtocolType::TCP, 200);
        stats.record_packet(ProtocolType::UDP, 50);
        stats.record_packet(ProtocolType::DNS, 80);

        auto dist = stats.get_protocol_distribution();
        REQUIRE(dist["TCP"] == 2);
        REQUIRE(dist["UDP"] == 1);
        REQUIRE(dist["DNS"] == 1);
        REQUIRE(dist.find("HTTP") == dist.end());
    }

    SECTION("Reset limpia todo") {
        stats.record_packet(ProtocolType::TCP, 100);
        stats.reset();

        REQUIRE(stats.total_packets.load() == 0);
        REQUIRE(stats.total_bytes.load() == 0);
        auto dist = stats.get_protocol_distribution();
        REQUIRE(dist.empty());
    }
}

TEST_CASE("CaptureStats: concurrencia lock-free", "[stats][threading]") {
    CaptureStats stats;
    const int PER_THREAD = 50000;
    const int NUM_THREADS = 4;

    // Múltiples hilos escriben simultáneamente
    std::vector<std::thread> threads;
    for (int t = 0; t < NUM_THREADS; ++t) {
        threads.emplace_back([&, t] {
            ProtocolType proto = (t % 2 == 0) ? ProtocolType::TCP : ProtocolType::UDP;
            for (int i = 0; i < PER_THREAD; ++i) {
                stats.record_packet(proto, 64);
            }
        });
    }

    for (auto& th : threads) {
        th.join();
    }

    REQUIRE(stats.total_packets.load() == NUM_THREADS * PER_THREAD);
    REQUIRE(stats.total_bytes.load() == NUM_THREADS * PER_THREAD * 64ULL);

    auto dist = stats.get_protocol_distribution();
    REQUIRE(dist["TCP"] + dist["UDP"] == static_cast<uint64_t>(NUM_THREADS * PER_THREAD));
}
