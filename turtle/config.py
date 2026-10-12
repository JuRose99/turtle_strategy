from dataclasses import dataclass
import yaml

@dataclass
class DataConfig:
    path:str
    date_col: str = "date"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"

@dataclass
class StrategyConfig:
    entry_period: int = 20
    exit_period: int = 10
    atr_period: int = 10
    atr_multiple: float = 2.0
    risk_pct: float = 0.02
    allow_short: bool = False

@dataclass
class BacktestConfig:
    initial_cash: float = 100000
    fee_rate: float = 1e-4
    slippage: float = 2e-4
    lot_size: int = 100

@dataclass
class OutputConfig:
    save_dir: str = "outputs"
    show_plot: bool = True

@dataclass
class Config:
    data: DataConfig
    strategy: StrategyConfig
    backtest: BacktestConfig
    output: OutputConfig

def load_config(path: str = "config.yaml") -> Config:
    with open(path,"r",encoding='utf-8') as f:
        raw = yaml.safe_load(f)
    return Config(
        data=DataConfig(**raw["data"]),
        strategy=StrategyConfig(**raw["strategy"]),
        backtest=BacktestConfig(**raw["backtest"]),
        output=OutputConfig(**raw.get("output",{}))
    )