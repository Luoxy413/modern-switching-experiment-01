
"""实验一：包头大小变化分析（32 bit → 16 bit）。"""

from pathlib import Path
import sys
import csv
import json

# 保证可以从项目根目录导入 src 模块
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.models import Config
from src.utils import make_traffic, simulate
from src.metrics import summarize
from src.performance_test import SCENARIOS


# 附加实验结果保存目录
OUTPUT = ROOT / "results" / "extra"


def run_experiment(cfg):
    """用指定的 Config 完成四场景、两模型仿真。"""

    rows = []
    traces = {}

    for scenario in SCENARIOS:
        # 生成当前场景的业务数据
        arrivals = make_traffic(scenario, cfg)

        # 同一组到达记录用于两种交换方式
        for mode in ("circuit", "packet"):
            raw = simulate(arrivals, cfg, mode)
            metrics = summarize(raw, cfg)

            rows.append({
                "scenario": scenario,
                "mode": mode,
                **metrics
            })

            traces[f"{scenario}/{mode}"] = raw

    return rows, traces


def save_csv(path, rows):
    """保存 CSV 文件。"""

    with path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=list(rows[0].keys())
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # 1. 创建两组配置
    cfg32 = Config(header_bits=32)
    cfg16 = Config(header_bits=16)

    # 2. 运行两组实验
    rows32, _ = run_experiment(cfg32)
    rows16, traces16 = run_experiment(cfg16)

    # 3. 读取已有基线，检查是否与重新运行一致
    baseline_path = ROOT / "results" / "comparison.json"

    with baseline_path.open(encoding="utf-8") as f:
        baseline = json.load(f)

    assert baseline["config"] == cfg32.__dict__, (
        "原始配置与本次基线配置不一致"
    )

    assert baseline["rows"] == rows32, (
        "重新运行的32 bit结果与原始基线不一致"
    )

    # 4. 保存16 bit实验结果
    save_csv(
        OUTPUT / "header16_comparison.csv",
        rows16
    )

    with (OUTPUT / "header16_comparison.json").open(
        "w", encoding="utf-8"
    ) as f:
        json.dump(
            {
                "config": cfg16.__dict__,
                "rows": rows16,
                "traces": traces16
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    # 5. 生成参数对比表
    comparison = []

    for old, new in zip(rows32, rows16):
        assert old["scenario"] == new["scenario"]
        assert old["mode"] == new["mode"]

        comparison.append({
            "scenario": old["scenario"],
            "mode": old["mode"],
            "header32_payload_utilization":
                old["payload_utilization"],
            "header16_payload_utilization":
                new["payload_utilization"],
            "header32_wire_utilization":
                old["wire_utilization"],
            "header16_wire_utilization":
                new["wire_utilization"],
            "header32_mean_delay_ms":
                old["mean_delay_ms"],
            "header16_mean_delay_ms":
                new["mean_delay_ms"],
            "header32_loss_ratio":
                old["loss_ratio"],
            "header16_loss_ratio":
                new["loss_ratio"],
            "header32_backlog_bits":
                old["backlog_payload_bits"],
            "header16_backlog_bits":
                new["backlog_payload_bits"]
        })

    save_csv(
        OUTPUT / "header_sensitivity.csv",
        comparison
    )

    # 6. 打印简要结果
    print("\n包头参数变化实验完成！")
    print("基线：32 bit")
    print("附加：16 bit")
    print("\n结果保存位置：", OUTPUT)

    for item in comparison:
        print(
            item["scenario"],
            item["mode"],
            "有效利用率:",
            round(
                item["header32_payload_utilization"] * 100,
                2
            ),
            "% →",
            round(
                item["header16_payload_utilization"] * 100,
                2
            ),
            "%"
        )


if __name__ == "__main__":
    main()
