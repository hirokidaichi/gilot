import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


TITLE_SIZE = 15


def gini(x):
    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    rmad = mad / np.mean(x)
    # Gini coefficient
    return 0.5 * rmad


def lorenz(v):
    x = np.linspace(0., 100., 21)
    total = np.sum(v, dtype=np.float64)
    y = []
    for xi in x:
        yi_vals = v[v <= np.percentile(v, xi)]
        yi = (np.sum(yi_vals) / total) * 100.0
        y.append(yi)
    return x, y


def _ts_to_string(ts):
    pattern = r"(\d+)([a-zA-Z])"
    r = re.match(pattern, ts)
    MAP = dict(W="Weeks", D="Days", M="Months", Y="Years")
    unit = MAP[r.group(2).upper()]
    count = r.group(1)
    return f"{count} {unit}"


def _in_sprint(df, timeslot="2W"):
    if len(df) == 0:
        empty_df = pd.DataFrame([], columns=df.columns)
        empty_df["date"] = pd.to_datetime([])
        empty_df.set_index("date", inplace=True)
        empty_df["authors"] = 0
        empty_df["addedlines"] = 0
        return empty_df
    df_resampled = df.resample(timeslot).sum()
    df_resampled["authors"] = df["author"].resample(timeslot).nunique()
    df_resampled["addedlines"] = 0
    return df_resampled


def _plot_gini(df, plt):
    v = df.lines.values
    bins, result = lorenz(v)
    gi = gini(v)
    plt.plot(bins, result, label="commit")
    plt.plot(bins, bins, '--', label="perfect equality")
    plt.xlabel("Percentile")
    plt.ylabel("Ratio")
    plt.xlim(0, 100)
    plt.fill_between(bins, bins, result, color="blue", alpha=0.2)
    plt.fill_between(bins, result, color="red", alpha=0.2)
    title_label = f"GINI COEFFICIENT: {gi:.1%}"
    plt.title(title_label, fontsize=TITLE_SIZE)
    plt.legend()
    pass


def _plot_hist(df, plt, ts):
    v = df.lines.values
    median = np.median(v)
    timeslot = _ts_to_string(ts)
    # 非推奨API回避: pandas+matplotlibでヒストグラム描画
    plt.hist(v, bins='auto', color='C0', alpha=0.7, edgecolor='black')
    plt.xlim(0,)

    plt.title("Histgram of Code Output", fontsize=TITLE_SIZE)
    _plot_text(plt, f"median={int(median) :,d} lines")
    plt.ylabel("")
    plt.xlabel(f"Code Output in {timeslot}")


def _plot_text(plt, text):
    ax = plt.gca()
    plt.text(0.99, 0.1, text,
             horizontalalignment='right',
             verticalalignment='top',
             bbox=dict(facecolor='#cccccc', alpha=0.5),
             transform=ax.transAxes)


def _plot_authors(df, plt):
    date = df.index.values
    authors = df["authors"]
    mean = authors.mean()
    plt.title(" Number of Actual Authors", fontsize=TITLE_SIZE)
    plt.plot(date, authors, marker=".", label="commit authors")
    plt.plot(date, np.ones(len(authors)) * mean, "--", label="mean")
    _plot_text(plt, f"mean = {mean :.1f} authors/timeslot")
    plt.xlim(date[0], date[-1])
    plt.ylabel("Unique number of committed author")
    plt.legend()


def _plot_code(df, plt):
    date = df.index.values
    total_change = df.lines.sum()
    total_added = (df.insertions - df.deletions).sum()
    refactor = 1 - total_added / total_change
    plt.title("Code Output and Productivity", fontsize=TITLE_SIZE)
    plt.plot(date, df.lines, label="lines")
    plt.plot(date, df.insertions, color="g", label="insertions")
    plt.plot(date, df.deletions, color="r", label="deletions")
    _plot_text(
        plt,
        f"lines={total_change:,d} ,added={total_added:,d}, refactor={refactor:.2f}")
    plt.xlim(date[0], date[-1])
    plt.ylabel("Lines")
    plt.fill_between(
        date,
        df.insertions,
        df.deletions,
        where=df.insertions >= df.deletions,
        color="g",
        alpha=0.5,
        interpolate=True)
    plt.fill_between(
        date,
        df.insertions,
        df.deletions,
        where=df.insertions < df.deletions,
        color="r",
        alpha=0.5,
        interpolate=True)
    plt.legend()
    _plot_productivity(df,plt)


def _plot_productivity(df,plt):
    time = 0.5  # 2 weeks mostly 0.5 months
    beta = 0.3
    df["effort"] = df["authors"] * time
    effort = df["effort"]
    s_time = time ** (4 / 3)
    s_effort = (effort / beta)**(1 / 3)
    s_size = np.maximum(df["insertions"] - df["deletions"],df["lines"] / 2) * 0.7
    prod = s_size / (s_effort * s_time)
    level = prod_to_level(prod)
    max_level = int(level.max() + 3)
    df["level"] = level.rolling(3,center=True).mean()
    ax = plt.gca()
    ax2 = ax.twinx()
    ax2.grid(False)
    date = df.index.values
    ax2.plot(date,df["level"],color="gray",linestyle="--",marker="x")
    ax2.set_ylim([0, max_level])


def prod_to_level(prod) :
    a = 600.7669
    b = 1.272067
    return np.maximum(np.log(prod / a) / np.log(b),0)


def plot(df, timeslot='2W', output=False, name="[This Graph]"):
    sns.set()
    suptitle = f"{name} : created by 'gilot'"
    dfs = _in_sprint(df, timeslot=timeslot)
    plt.figure(figsize=(16, 9))
    plt.tight_layout(pad=0.05, w_pad=0)
    plt.suptitle(suptitle, fontsize=13, y=0.95, x=0.8)
    plt.subplots_adjust(wspace=0.15, hspace=0.4)
    # PLOT GINI / LORENTZ
    plt.subplot(2, 2, 1)
    _plot_gini(dfs, plt)

    # PlOT HIST
    plt.subplot(2, 2, 3)
    _plot_hist(dfs, plt, timeslot)

    # PLOT CODE
    plt.subplot(2, 2, 2)
    _plot_code(dfs, plt)

    # PLOT AUTHORS
    plt.subplot(2, 2, 4)
    _plot_authors(dfs, plt)
    if(output):
        plt.savefig(output, dpi=150, bbox_inches='tight')
    else:
        plt.show()


def info(df, timeslot="2W"):
    rdf = _in_sprint(df, timeslot)
    desc = rdf.describe().drop("count")
    dic = desc.to_dict()
    sdf = df.sum()
    lines = int(sdf.lines)
    added = int(sdf.insertions - sdf.deletions)
    
    # 0による除算を防ぐ
    if lines == 0:
        refactor = 0
    else:
        refactor = 1 - added / lines
        
    output = dict(lines=lines, added=added, refactor=refactor)
    return output


def _top_authors(df,num):
    return df.author.value_counts()[:num].index.tolist()


def _count_commits(df, top=15, only=None):
    authors = only if only else _top_authors(df,top)
    index = df.resample("1W").sum().index
    result = pd.DataFrame([],index=index , columns=[*authors,'Others'])

    for a in authors:
        result[a] = df["hexsha"][df.author == a].resample("1W").nunique()

    result["Others"] = df["hexsha"][~df.author.isin(authors)].resample("1W").nunique()

    result.fillna(value=0,inplace=True)
    return result


def _commit_ratio(df):
    def ratio(s):
        total = np.sum(s)
        if total == 0:
            return s * 0.0
        return s / total
    return df.apply(ratio, axis=1)


def authors(df, output=False, top=None, name="--", only=None):
    sns.set_style("darkgrid")
    plt.rcParams["font.family"] = "IPAGothic"
    result = _count_commits(df, top=top, only=only)

    fig = plt.figure(figsize=(16, 9))
    plt.suptitle(f"GIT LOG {name} AUTHORS REPORT created by gilot", fontsize=13, y=0.95, x=0.7)
    gs = fig.add_gridspec(10, 10)

    plt.tight_layout(pad=0.05, w_pad=0)

    plt.subplot(gs[0:5,0:8])
    plt.ylabel("number of commits")
    plt.title("Changes in the number of commits (stack graph by author)")
    result.plot.area(ax=plt.gca(), colormap="Spectral")
    plt.legend(loc='upper left', bbox_to_anchor=(1.0, 1.01))
    plt.xlabel("")
    plt.subplot(gs[5:10,0:8])
    plt.ylabel("commit ratio")
    ratio = _commit_ratio(result)
    ratio.plot.area(ax=plt.gca(), colormap="Spectral",legend=None)
    plt.ylim(0,1)
    if(output):
        plt.savefig(output, dpi=150, bbox_inches='tight')
    else:
        plt.show()
