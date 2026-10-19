"""任务1：补全固定时隙电路交换发送。只改本文件内TODO。"""
def serve_circuit(queues, tick, cfg):
    """queues为每用户一个deque[Pending]，原地更新。
    本tick只能服务user=tick % cfg.users，其他用户不能借用其时隙。
    该用户可在slot_bits预算内连续发送多个记录，也可部分发送一个记录。
    返回(本tick实际线速发送比特数, 本tick完整发送的Pending列表)。
    空队列返回(0,[])；记录完全发完才pop并记入完成列表。
    提示：先确定用户，再在该用户队列上按FIFO扣减remaining_wire_bits。
    """
    
def serve_circuit(queues, tick, cfg):
    """固定时隙电路交换：每个 tick 只服务指定用户。"""

    # 1. 计算当前允许使用时隙的用户
    user = tick % cfg.users

    # 2. 获取该用户的待发送队列
    queue = queues[user]

    # 3. 初始化当前 tick 的剩余发送容量
    budget = cfg.slot_bits

    # 4. 记录实际发送量及完成的记录
    wire_bits = 0
    completed_records = []

    # 5. 有剩余容量并且队列不为空时，继续发送
    while budget > 0 and queue:

        # 取队首记录，但暂时不删除
        record = queue[0]

        # 本次最多能发送的数据量
        sent = min(budget, record.remaining_wire_bits)

        # 更新记录剩余数据量
        record.remaining_wire_bits -= sent

        # 更新本 tick 剩余容量
        budget -= sent

        # 统计实际发送量
        wire_bits += sent

        # 只有整条记录发送完成，才能移出队列
        if record.remaining_wire_bits == 0:
            completed_records.append(queue.popleft())

    # 6. 返回发送量和完成记录
    return wire_bits, completed_records

