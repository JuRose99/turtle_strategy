from typing import List
import numpy as np
import pandas as pd

from .backtest import Trade


def compute_metrics(equity: pd.Series,
                    trades: List[Trade],
                    initial_cash: float) -> dict:
    total_ret = equity.iloc[-1] / initial_cash - 1
    n_days = (equity.index[-1] - equity.index[0]).days
    ann_ret = (1 + total_ret) ** (365 / n_days) - 1 if n_days > 0 else np.nan

    dd = equity / equity.cummax() - 1
    max_dd = dd.min()

    daily = equity.pct_change().dropna()
    sharpe = (daily.mean() / daily.std() * np.sqrt(252)) if daily.std() > 0 else np.nan
    calmar = ann_ret / abs(max_dd) if max_dd != 0 else np.nan

    n = len(trades)
    if n > 0:
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        win_rate = len(wins) / n
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0.0
        avg_loss = abs(np.mean([t.pnl for t in losses])) if losses else 0.0
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = (sum(t.pnl for t in wins) / gross_loss) if gross_loss > 0 else np.inf
        avg_hold = float(np.mean([t.holding_days for t in trades]))
    else:
        win_rate = avg_win = avg_loss = profit_factor = avg_hold = np.nan

    return {
        "total_return": total_ret,
        "annual_return": ann_ret,
        "max_drawdown": max_dd,
        "sharpe": sharpe,
        "calmar": calmar,
        "num_trades": n,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "avg_holding_days": avg_hold,
    }


def format_metrics(m: dict) -> str:
    return (
        f"total_return: {m['total_return']*100:.2f}% | "
        f"annual_return: {m['annual_return']*100:.2f}% | "
        f"max_drawdown: {m['max_drawdown']*100:.2f}% | "
        f"sharpe: {m['sharpe']:.2f} | "
        f"calmar: {m['calmar']:.2f} | "
        f"num_trades: {m['num_trades']} | "
        f"win_rate: {m['win_rate']*100:.1f}% | "
        f"profit_factor: {m['profit_factor']:.2f} | "
        f"avg_holding_days: {m['avg_holding_days']:.1f} days"
    )