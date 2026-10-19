"""任务2：补全共享FIFO分组交换发送。"""
def serve_packet(queue, tick, cfg):
    """queue为共享deque[Pending]，原地更新。
    remaining_wire_bits已由框架初始化为payload_bits+header_bits，不再重复加包头。
    每tick发送不超过slot_bits；必须发完队首再处理下一项。
    分组允许跨tick续传，但不得与其他分组交错，不能因大于一个时隙就丢弃。
    返回(线速发送比特数,完整发送的Pending列表)；空队列返回(0,[])。
    """
    
def serve_packet(queue, tick, cfg):
    """共享 FIFO 分组交换发送函数。"""

    # 1. 当前 tick 的发送容量
    budget = cfg.slot_bits

    # 2. 实际发送量
    wire_bits = 0

    # 3. 当前 tick 完成的记录
    completed_records = []

    # 4. 队列非空且还有发送容量时继续发送
    while budget > 0 and queue:

        # 获取队首记录
        record = queue[0]

        # 计算本次能够发送多少 bit
        sent = min(budget, record.remaining_wire_bits)

        # 更新记录剩余数据量
        record.remaining_wire_bits -= sent

        # 扣除已经使用的发送容量
        budget -= sent

        # 累加实际发送量
        wire_bits += sent

        # 完整发送后才从队列删除
        if record.remaining_wire_bits == 0:
            completed_records.append(queue.popleft())

    # 5. 返回发送量和完成记录
    return wire_bits, completed_records

