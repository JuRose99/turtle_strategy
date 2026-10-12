"""turtle/plot.py - Backtest visualization."""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
from matplotlib.colors import TwoSlopeNorm

from .backtest import BacktestResult


# ------------------------------------------------------------- setup

_FONTS = ["SimHei", "Microsoft YaHei", "PingFang SC", "Heiti SC",
          "WenQuanYi Zen Hei", "Noto Sans CJK SC", "Arial Unicode MS"]


def _setup():
    avail = {f.name for f in fm.fontManager.ttflist}
    for n in _FONTS:
        if n in avail:
            plt.rcParams["font.sans-serif"] = [n]
            break
    plt.rcParams.update({
        "axes.unicode_minus": False,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#cccccc",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#e8e8e8",
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "normal",   # SimHei has no bold; keep normal
    })


_setup()


def _xaxis(ax):
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


# ------------------------------------------------------------- chart 1

def _fig_main(df, result, cash, path=None):
    eq = result.equity
    fig, ax = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                           gridspec_kw={"height_ratios": [3, 2]})

    a = ax[0]
    a.plot(df["date"], df["close"], color="#2c3e50", lw=1.2,
           label="Close", zorder=2)
    for col, c, lbl in (("upper", "#3498db", "Upper"),
                        ("lower", "#e67e22", "Lower")):
        if col in df.columns:
            a.plot(df["date"], df[col], color=c, lw=0.9,
                   alpha=0.55, label=lbl, zorder=1)
    if result.buy_dates:
        a.scatter(result.buy_dates, result.buy_prices, marker="^", s=70,
                  color="#e74c3c", edgecolor="white", linewidth=0.8,
                  label="Buy", zorder=3)
    if result.sell_dates:
        a.scatter(result.sell_dates, result.sell_prices, marker="v", s=70,
                  color="#27ae60", edgecolor="white", linewidth=0.8,
                  label="Sell", zorder=3)
    a.set_ylabel("Price")
    a.set_title("Price & Signals")
    a.legend(loc="upper left", fontsize=9, ncol=3)

    a = ax[1]
    a.plot(eq.index, eq.values, color="#2980b9", lw=1.4,
           label="Strategy", zorder=2)
    a.axhline(cash, color="#95a5a6", ls="--", lw=0.9,
              label="Initial", zorder=1)
    ps = df.set_index("date")["close"].reindex(eq.index, method="ffill").dropna()
    if len(ps):
        a.plot(ps.index, ps / ps.iloc[0] * cash, color="#7f8c8d",
               lw=1.0, alpha=0.85, label="Buy & Hold", zorder=1)
    a.set_ylabel("Equity")
    a.set_title("Equity Curve")
    a.legend(loc="upper left", fontsize=9, ncol=3)
    _xaxis(a)

    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


# ------------------------------------------------------------- chart 2

def _fig_drawdown(eq, path=None):
    fig, ax = plt.subplots(figsize=(13, 3.5))
    dd = (eq / eq.cummax() - 1) * 100

    ax.fill_between(dd.index, dd.values, 0, color="#e74c3c", alpha=0.25)
    ax.plot(dd.index, dd.values, color="#c0392b", lw=1.1)

    if len(dd):
        i = dd.idxmin()
        ax.scatter([i], [dd.min()], color="#c0392b", s=40, zorder=3)
        ax.annotate(f"Max DD {dd.min():.2f}%", xy=(i, dd.min()),
                    xytext=(10, 8), textcoords="offset points",
                    fontsize=9, color="#c0392b")

    ax.set_ylabel("Drawdown (%)")
    ax.set_title("Drawdown")
    _xaxis(ax)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


# ------------------------------------------------------------- chart 3

def _fig_analytics(eq, path=None):
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))

    # --- yearly returns ---
    a = ax[0]
    y = eq.groupby(eq.index.year).last()
    prev = y.shift(1)
    if len(y):
        prev.iloc[0] = eq.iloc[0]
    yr = (y / prev - 1).dropna() * 100

    if len(yr):
        bars = a.bar([str(i) for i in yr.index], yr.values,
                     color=["#27ae60" if v >= 0 else "#e74c3c" for v in yr.values],
                     alpha=0.85, edgecolor="white", width=0.55)

        vmin, vmax = float(yr.min()), float(yr.max())
        span = max(vmax - vmin, 1.0)
        a.set_ylim(vmin - span * 0.22, vmax + span * 0.18)
        a.axhline(0, color="#555", lw=0.8)

        for b, v in zip(bars, yr.values):
            offset = span * 0.04
            if v >= 0:
                a.text(b.get_x() + b.get_width() / 2, v + offset,
                       f"{v:.1f}%", ha="center", va="bottom",
                       fontsize=8, color="#1e7a44")
            else:
                a.text(b.get_x() + b.get_width() / 2, v - offset,
                       f"{v:.1f}%", ha="center", va="top",
                       fontsize=8, color="#b03a2e")
    else:
        a.text(0.5, 0.5, "No data", ha="center", va="center",
               transform=a.transAxes, color="gray")

    a.set_title("Yearly Returns (%)")
    a.set_ylabel("Return (%)")
    a.tick_params(axis="x", labelsize=9)

    # --- monthly heatmap ---
    a = ax[1]
    t = pd.DataFrame({"y": eq.index.year, "m": eq.index.month, "v": eq.values})
    m = t.groupby(["y", "m"])["v"].last().sort_index()
    r = m / m.shift(1) - 1
    if len(r):
        r.iloc[0] = m.iloc[0] / eq.iloc[0] - 1
    dfm = pd.DataFrame({"y": r.index.get_level_values(0),
                        "m": r.index.get_level_values(1),
                        "r": r.values})
    piv = dfm.pivot(index="y", columns="m", values="r").reindex(columns=range(1, 13))

    if not piv.empty:
        data = piv.values * 100
        finite = data[np.isfinite(data)]
        vmax = max(np.abs(finite).max() if finite.size else 1, 1)

        im = a.imshow(data, cmap="RdYlGn", aspect="auto",
                      norm=TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax))

        # disable cursor readout to avoid OverflowError on inf/nan hover
        a.format_coord = lambda x, y: ""

        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                if np.isfinite(data[i, j]):
                    a.text(j, i, f"{data[i, j]:.1f}", ha="center",
                           va="center", fontsize=7, color="#333")
        a.set_xticks(range(12))
        a.set_xticklabels(range(1, 13))
        a.set_yticks(range(len(piv.index)))
        a.set_yticklabels(piv.index)
        a.set_xlabel("Month")
        a.grid(False)
    else:
        a.text(0.5, 0.5, "No data", ha="center", va="center",
               transform=a.transAxes, color="gray")
        a.set_xticks([])
        a.set_yticks([])
        a.format_coord = lambda x, y: ""

    a.set_title("Monthly Returns (%)")

    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


# ------------------------------------------------------------- chart 4

def _fig_trades(result, path=None):
    fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
    tr = result.trades

    if not tr:
        for a in ax:
            a.text(0.5, 0.5, "No trades", ha="center", va="center",
                   transform=a.transAxes, color="gray")
            a.set_xticks([])
            a.set_yticks([])
        fig.tight_layout()
        if path:
            fig.savefig(path, dpi=150, bbox_inches="tight")
        return fig

    pnl = np.array([t.pnl for t in tr])
    hold = np.array([t.holding_days for t in tr])

    a = ax[0]
    a.bar(range(1, len(pnl) + 1), pnl,
          color=["#27ae60" if p >= 0 else "#e74c3c" for p in pnl],
          alpha=0.85, edgecolor="white")
    a.axhline(0, color="#555", lw=0.8)
    a.set_title(f"Per-Trade PnL ({len(pnl)} trades)")
    a.set_xlabel("Trade")
    a.set_ylabel("PnL")

    a = ax[1]
    a.hist(hold, bins=min(25, max(5, len(hold) // 3)),
           color="#f39c12", alpha=0.85, edgecolor="white")
    a.axvline(hold.mean(), color="#c0392b", lw=1.3,
              label=f"Mean {hold.mean():.1f} d")
    a.set_title("Holding Days")
    a.set_xlabel("Days")
    a.legend(fontsize=9)

    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


# ------------------------------------------------------------- entry

def plot_result(df, result: BacktestResult, initial_cash: float,
                save_dir=None, show: bool = True) -> None:
    """Generate backtest charts into `save_dir`."""
    if result.equity is None or len(result.equity) == 0:
        print("[plot] Empty equity, skip plotting.")
        return

    out = Path(save_dir) if save_dir else None
    if out:
        out.mkdir(parents=True, exist_ok=True)

    figs = [
        _fig_main(df, result, initial_cash,
                  out / "chart_main.png" if out else None),
        _fig_drawdown(result.equity,
                      out / "chart_drawdown.png" if out else None),
        _fig_analytics(result.equity,
                       out / "chart_analytics.png" if out else None),
        _fig_trades(result,
                    out / "chart_trades.png" if out else None),
    ]

    if show:
        plt.show()
    for f in figs:
        plt.close(f)