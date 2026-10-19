
"""学生自拟反例：验证电路交换不能借用其他用户的空闲时隙。"""

from src.models import Config, Pending, new_queues
from src.part1_circuit import serve_circuit


def test_my_case():
    # 1. 创建仿真配置
    cfg = Config(
        users=3,
        ticks=3,
        slot_bits=128,
        tick_ms=1.0
    )

    # 2. 创建三个用户的独立队列
    queues = new_queues(cfg.users)

    # 用户0没有数据

    # 用户1有64 bit数据
    queues[1].append(
        Pending(
            user=1,
            arrival_tick=0,
            payload_bits=64,
            remaining_wire_bits=64
        )
    )

    # 用户2有96 bit数据
    queues[2].append(
        Pending(
            user=2,
            arrival_tick=0,
            payload_bits=96,
            remaining_wire_bits=96
        )
    )

    # 3. tick 0：只能服务用户0
    wire0, completed0 = serve_circuit(queues, 0, cfg)

    assert wire0 == 0
    assert completed0 == []
    assert len(queues[1]) == 1
    assert len(queues[2]) == 1
    assert queues[1][0].remaining_wire_bits == 64
    assert queues[2][0].remaining_wire_bits == 96

    # 4. tick 1：服务用户1
    wire1, completed1 = serve_circuit(queues, 1, cfg)

    assert wire1 == 64
    assert len(completed1) == 1
    assert completed1[0].user == 1
    assert len(queues[1]) == 0
    assert len(queues[2]) == 1
    assert queues[2][0].remaining_wire_bits == 96

    # 5. tick 2：服务用户2
    wire2, completed2 = serve_circuit(queues, 2, cfg)

    assert wire2 == 96
    assert len(completed2) == 1
    assert completed2[0].user == 2
    assert len(queues[2]) == 0

    # 6. 验证总发送量
    assert wire0 + wire1 + wire2 == 160
