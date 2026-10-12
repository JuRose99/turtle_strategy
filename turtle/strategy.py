import pandas as pd
import numpy as np

from .config import StrategyConfig


def compute_indicators(df: pd.DataFrame, cfg: StrategyConfig) -> pd.DataFrame:
    out = df.copy()

    prev_close = out["close"].shift(1)

    # True Range：max(high-low, |high-prev_close|, |low-prev_close|)
    tr = np.maximum(
        out["high"] - out["low"],
        np.maximum(
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ),
    )
    out["atr"] = tr.rolling(cfg.atr_period).mean().shift(1)
    out["upper"] = out["high"].rolling(cfg.entry_period).max().shift(1)
    out["lower"] = out["low"].rolling(cfg.exit_period).min().shift(1)

    return out