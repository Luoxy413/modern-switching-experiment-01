# AI协作记录

工具与模型：ChatGPT（用于理解和实现电路交换、分组交换、指标统计、自拟测试及包头参数变化实验；具体模型版本未确认，故不猜测）。Codex 实际读取当前工作区的代码、测试、基线结果、附加实验结果和 PRD，并编辑 `REPORT.md`、`AI_LOG.md`；未修改 `src/`、`scripts/header_experiment.py`、`grading/`、测试脚本或任何 `results/` 产物。

## 一项真实协作过程

需求与输入：需求是用同一组到达业务比较固定时隙电路交换与共享 FIFO 分组交换，补全 `serve_circuit()`、`serve_packet()` 和 `summarize()`，并以自拟反例检查边界。随后为完成 PRD 第 11.11 节的参数变化分析，比较基线 `header_bits=32` 与附加配置 `header_bits=16`；其他配置均保持为 4 用户、256 tick、每 tick 128 bit、4096 bit payload 缓存，随机业务种子为 2026。模型合同明确规定：到达先于发送；电路交换的服务用户为 `tick % users`；分组记录只在准入时增加一次包头；未完成记录在有限观察窗口结束时计积压而不计丢失。

AI建议：

- `serve_circuit()`：先由 `tick % cfg.users` 唯一确定可服务队列；在该队列中按 FIFO 用 `min(budget, remaining_wire_bits)` 发送，只有整条记录发完才出队。
- `serve_packet()`：仅服务共享 FIFO 的队首，保留跨 tick 的 `remaining_wire_bits`，本 tick 若发完队首且还有预算则继续下一条；包头已在准入时包含在剩余线速比特中，不能在续传时重复相加。
- `summarize()`：先检查 `generated = delivered + dropped + backlog`，再分别计算 payload 利用率、wire 利用率、完成记录的时延、丢失率和积压；没有完成记录时，时延应为 `None` 而非 0。
- 包头参数实验：按用户提供的实际协作信息，ChatGPT 建议新建独立的 `scripts/header_experiment.py`，复用原有 `Config`、业务生成、仿真和指标函数，以两组 `Config(header_bits=32)`、`Config(header_bits=16)` 生成结果；先断言重新计算的 32 bit 行等于既有基线，再将 16 bit 结果和敏感性表写入 `results/extra/`。

我的手算与测试：

1. 两用户手算按后补充的《实验一 PRD》第 6.1 节：2 用户、2 tick、每 tick 128 bit、包头 32 bit，只有 tick 0 的用户 1 到达一条 96 bit 记录。手算预期为：电路交换 tick 0 因服务用户 0 而闲置，tick 1 发送 96 bit，并在 2 ms 完成；分组交换在 tick 0 发送 `96+32=128` bit，并在 1 ms 完成。二者有效载荷利用率均为 `96/256=37.5%`，线路忙碌率分别为 37.5% 和 50%。完整推演见 `REPORT.md`；该例验证“相同有效利用率不代表相同时延”。

2. 自拟反例 `student_tests/test_my_case.py`：3 个用户、3 个 tick；用户 0 为空，用户 1 有 64 bit、用户 2 有 96 bit。手算预期依次为 `(wire0, wire1, wire2)=(0,64,96)`，总量 160 bit，且 tick 0 不改变用户 1、2 的记录。断言检查发送量、完成用户、队列长度和剩余量。这针对错误地借用空闲固定时隙，而不是一般的吞吐率比较。

3. 用户此前实际完成并报告的结果（本次开始前的既有信息）：虚拟环境配置与框架测试 4 passed；电路测试 4 passed；分组测试 4 passed；指标测试 3 passed；三个核心函数联合测试 11 passed；`src/performance_test.py` 曾运行并生成 CSV、JSON 和三张 PNG；集成测试 3 passed；自拟测试 1 passed。

4. Codex 本次重新验证的结果：先尝试系统 `python -m pytest`，其仅报告“没有 pytest 模块”，因此不属于项目测试结果；随后用工作区 `.venv\\Scripts\\python.exe` 运行 `grading/test_framework.py`、`grading/test_circuit.py`、`grading/test_packet.py`、`grading/test_metrics.py`、`grading/test_integration.py` 和 `student_tests/test_my_case.py`，输出为 **19 passed in 0.23s**。该次没有运行 `src/performance_test.py`，以免覆盖已有基线结果。

5. 用户此前在 VS Code 实际完成的包头参数实验（本次开始前的既有信息）：创建并运行 `scripts/header_experiment.py`；生成 `results/extra/header16_comparison.csv`、`header16_comparison.json` 和 `header_sensitivity.csv`；比较 32 bit 与 16 bit 头部下的有效载荷利用率；并运行综合测试，终端输出为 **15 passed in 0.08s**。这是用户报告的历史运行结果，不是 Codex 本次新执行的测试。

6. Codex 本次文档整理只读取并交叉核对附加实验脚本、两个比较 CSV 和两个 JSON；没有重新运行 `scripts/header_experiment.py`、`src/performance_test.py` 或测试命令，也没有覆盖已有结果文件。`header_sensitivity.csv` 不含最大时延，报告中的最大时延比较来自同一附加实验的 `header16_comparison.csv` 和基线 `comparison.csv`。

修正或采纳理由：这些做法直接满足模型合同的服务顺序、缓存准入和有限窗口要求。固定时隙只读一个用户队列，能防止用户 0 空闲时用户 1、2 抢占；共享队首不被跳过，能维持 FIFO；守恒式把窗口末全部未完成记录作为积压，能防止把尚可继续发送的数据误报为丢失。参数实验采用独立脚本而不是修改 `src/models.py` 的默认包头，可保护原始基线、保持除包头外所有条件一致、使结果可复现，并避免影响已通过测试的核心实现。即使实现首次已通过公开测试，仍用“空闲时隙不能借用”的具体边界反例检查最容易被错误泛化的规则。

我能解释的核心逻辑：

- 避免借用固定时隙：电路服务函数首先计算 `user=tick % cfg.users`，循环只读取 `queues[user]`，不会扫描其他用户队列。
- 避免重复添加包头：仿真框架在分组记录准入时一次性令 `remaining_wire_bits=payload_bits+header_bits`；每次服务仅递减该字段，跨 tick 不重置也不加头。
- 避免遗漏积压：记录只有 `remaining_wire_bits==0` 才能完成并释放原始 payload 预留；窗口结束时仍被预留的原始 payload 汇入 `backlog_payload_bits`，并用 `generated=delivered+dropped+backlog` 校验。
- 包头参数的作用范围：分组记录在准入时将 `payload_bits + header_bits` 写入 `remaining_wire_bits`。例如 96 bit payload 加 32 bit 头恰为 128 bit，改为 16 bit 头后为 112 bit；这能减少 wire 开销，但当两种长度都能在同一 tick 完成时，完成时延和有效载荷利用率未必变化。电路记录不含该包头，因此本次参数变化不应改变电路交换结果。
