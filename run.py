from pathlib import Path
import pandas as pd

from turtle.config import load_config
from turtle.data import load_data
from turtle.strategy import compute_indicators
from turtle.backtest import run_backtest
from turtle.metrics import compute_metrics, format_metrics
from turtle.plot import plot_result


def main(config_path: str = "config.yaml") -> None:
    cfg = load_config(config_path)

    df = load_data(cfg.data)
    df = compute_indicators(df, cfg.strategy)

    result = run_backtest(df, cfg.strategy, cfg.backtest)
    metrics = compute_metrics(result.equity, result.trades, cfg.backtest.initial_cash)

    print("=" * 70)
    print(format_metrics(metrics))
    print(f"number of rejected signals: {result.rejected_signals}")
    print("=" * 70)

    out_dir = Path(cfg.output.save_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result.equity.to_csv(out_dir / "equity.csv", encoding="utf-8-sig")
    if result.trades:
        pd.DataFrame([t.__dict__ for t in result.trades]).to_csv(
            out_dir / "trades.csv", index=False, encoding="utf-8-sig"
        )

    plot_result(
        df, result, cfg.backtest.initial_cash,
        save_dir=out_dir,
        show=cfg.output.show_plot,
    )


if __name__ == "__main__":
    main()