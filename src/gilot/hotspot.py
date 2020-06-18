import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta


def remove_outer_lines(df : pd.DataFrame) -> pd.DataFrame:
    outer_sup = np.percentile(df["lines"].values,99.5)
    outer_sub = np.percentile(df["lines"].values,0.5)
    return df[(outer_sub < df["lines"]) & (df["lines"] < outer_sup)].copy()


def hotspot(df : pd.DataFrame) -> pd.DataFrame:
    df = remove_outer_lines(df)
    now = datetime.datetime.now()
    a_year = relativedelta(months=-12)
    last = now + a_year
    oldest = last - now

    df["ntd"] = 1 - (df.index - now) / oldest
    df.loc[df['ntd'] < 0,'ntd'] = 0
    score = 1 / (1 + np.exp((-12 * df["ntd"]) + 12))

    df["hotspot"] = score * np.log10(df["lines"])
    by_file = df.groupby("file_name").sum()
    by_file = by_file.drop(columns=["ntd"])
    by_file["authors"] = df.groupby("file_name").nunique()["author"]
    by_file["commits"] = df.groupby("file_name").nunique()["hexsha"]
    by_file["edit_rate"] = by_file["insertions"] / by_file["lines"]
    result = by_file.sort_values("hotspot",ascending=False)
    return result.loc[:, ['hotspot', 'commits', 'authors', 'edit_rate', "lines"]].copy()
