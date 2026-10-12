from dataclasses import dataclass, field
from typing import List
import pandas as pd

from .config import StrategyConfig, BacktestConfig


@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    shares: int
    pnl: float
    holding_days: int


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: List[Trade] = field(default_factory=list)
    rejected_signals: int = 0
    buy_dates: list = field(default_factory=list)
    buy_prices: list = field(default_factory=list)
    sell_dates: list = field(default_factory=list)
    sell_prices: list = field(default_factory=list)
    start_idx: int = 0


def run_backtest(df: pd.DataFrame, scfg: StrategyConfig, bcfg: BacktestConfig) -> BacktestResult:
    warmup = max(scfg.entry_period, scfg.exit_period, scfg.atr_period) + 1

    cash = bcfg.initial_cash
    shares = 0
    entry_price = 0.0
    entry_date = None
    stop_loss = 0.0

    equity_vals, equity_idx = [], []
    trades: List[Trade] = []
    rejected = 0
    buy_dates, buy_prices, sell_dates, sell_prices = [], [], [], []

    for i in range(warmup, len(df)):
        row = df.iloc[i]
        price = row["close"]
        equity_now = cash + shares * price

        if pd.isna(row["atr"]) or row["atr"] <= 0:
            equity_vals.append(equity_now)
            equity_idx.append(row["date"])
            continue

        # entrance
        if shares == 0 and price > row["upper"]:
            risk_amount = equity_now * scfg.risk_pct
            unit = scfg.atr_multiple * row["atr"]
            target = int(risk_amount / unit / bcfg.lot_size) * bcfg.lot_size

            if target < bcfg.lot_size:
                rejected += 1
            else:
                cost = target * price * (1 + bcfg.fee_rate + bcfg.slippage)
                if cost > cash:
                    per_lot = price * bcfg.lot_size * (1 + bcfg.fee_rate + bcfg.slippage)
                    target = int(cash / per_lot) * bcfg.lot_size
                    cost = target * price * (1 + bcfg.fee_rate + bcfg.slippage)

                if target >= bcfg.lot_size:
                    cash -= cost
                    shares = target
                    entry_price = price
                    entry_date = row["date"]
                    stop_loss = entry_price - scfg.atr_multiple * row["atr"]
                    buy_dates.append(row["date"])
                    buy_prices.append(entry_price)
                else:
                    rejected += 1

        # exit
        elif shares > 0:
            exit_line = stop_loss
            if pd.notna(row["lower"]):
                exit_line = max(stop_loss, row["lower"])

            if price < exit_line:
                proceeds = shares * price * (1 - bcfg.fee_rate - bcfg.slippage)
                cost_basis = shares * entry_price * (1 + bcfg.fee_rate + bcfg.slippage)
                cash += proceeds
                trades.append(Trade(
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=row["date"],
                    exit_price=price,
                    shares=shares,
                    pnl=proceeds - cost_basis,
                    holding_days=(row["date"] - entry_date).days,
                ))
                sell_dates.append(row["date"])
                sell_prices.append(price)
                shares = 0
                entry_price = 0.0
                entry_date = None
                stop_loss = 0.0

        equity_vals.append(cash + shares * price)
        equity_idx.append(row["date"])

    # After the retracement is over, if there are still open positions, force a liquidation at the last closing price
    if shares > 0:
        last = df.iloc[-1]
        price = last["close"]
        proceeds = shares * price * (1 - bcfg.fee_rate - bcfg.slippage)
        cost_basis = shares * entry_price * (1 + bcfg.fee_rate + bcfg.slippage)
        cash += proceeds
        trades.append(Trade(
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=last["date"],
            exit_price=price,
            shares=shares,
            pnl=proceeds - cost_basis,
            holding_days=(last["date"] - entry_date).days,
        ))
        sell_dates.append(last["date"])
        sell_prices.append(price)
        shares = 0
        # After closing the position, the net value of the last candlestick will be changed to the cash value after closing the position
        if equity_vals:
            equity_vals[-1] = cash

    # The data is too short, and no net value points have been generated
    if not equity_vals:
        return BacktestResult(
            equity=pd.Series(dtype=float, name="equity"),
            trades=[],
            rejected_signals=rejected,
            buy_dates=[], buy_prices=[], sell_dates=[], sell_prices=[],
            start_idx=warmup,
        )

    equity = pd.Series(
        equity_vals,
        index=pd.DatetimeIndex(equity_idx),
        name="equity",
    )

    return BacktestResult(
        equity=equity,
        trades=trades,
        rejected_signals=rejected,
        buy_dates=buy_dates,
        buy_prices=buy_prices,
        sell_dates=sell_dates,
        sell_prices=sell_prices,
        start_idx=warmup,
    )