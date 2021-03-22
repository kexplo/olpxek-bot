from typing import Any, Dict, IO, List, Union

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import mplfinance as mpf
import pandas as pd


def draw_upbit_chart(
    upbit_candles: List[Dict[str, Union[str, float, int]]], buf: IO[Any]
):
    df = pd.DataFrame(upbit_candles)
    df = df[
        [
            "candle_date_time_kst",
            "opening_price",
            "high_price",
            "low_price",
            "trade_price",
            "candle_acc_trade_volume",
        ]
    ]
    df = df.set_index("candle_date_time_kst")
    df.index = pd.to_datetime(df.index)
    df = df.reindex(index=df.index[::-1])
    fig, axlist = mpf.plot(
        df,
        columns=(
            "opening_price",
            "high_price",
            "low_price",
            "trade_price",
            "candle_acc_trade_volume",
        ),
        type="candle",
        mav=(15, 50),
        volume=True,
        style="yahoo",
        figscale=0.5,
        tight_layout=True,
        xrotation=0,
        datetime_format="%m/%d",
        fontscale=0.7,
        ylabel="",
        ylabel_lower="",
        returnfig=True,
    )
    axlist[0].yaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    fig.savefig(buf, bbox_inches="tight", format="png")
    plt.close(fig)
