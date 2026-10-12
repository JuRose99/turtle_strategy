from pathlib import Path
import pandas as pd

from .config import DataConfig

def load_data(cfg:DataConfig) -> pd.DataFrame:
    path = Path(cfg.path)
    if not path.exists():
        raise FileNotFoundError(f"File not found:{path.resolve()}")

    suffix = path.suffix.lower()
    if suffix in (".xlsx",".xls"):
        df = pd.read_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type:{suffix}")

    rename_map = {
        cfg.date_col:"date",
        cfg.open_col:"open",
        cfg.high_col:"high",
        cfg.low_col:"low",
        cfg.close_col:"close"
    }
    df = df.rename(columns={k: v for k,v in rename_map.items() if k in df.columns})

    required = {"date","high","low","close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns:{missing}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df