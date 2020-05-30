
import re
import git
import datetime
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()
from dateutil.relativedelta import relativedelta

DF_NULL = pd.DataFrame([],columns = ["date","hexsha","author","insertions","deletions","lines","files"])
DF_NULL.set_index("date", inplace=True)

TITLE_SIZE = 15

def dateformat(date) :
    return datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S")

def commit_to_dict(commit):
    # TODO 拡張子ごとにフィルタできたりしたほうがYAMLの編集とか入らないからいいだろうか。
    return dict(date=dateformat(commit.committed_date),
        hexsha=commit.hexsha,  author=commit.author.name, **commit.stats.total)

def log(repo, branch="origin/HEAD", since=datetime.date.today() - relativedelta(months=6)):
    return [commit_to_dict(c) for c in repo.iter_commits(branch, since= since )]

def _df_index(df):
    df.date = pd.to_datetime(df.date)
    df.set_index("date",inplace=True)
    return df
    
def dataframe(r,**kwargs) :
    logs = log(r, **kwargs)
    df = pd.DataFrame.from_records(logs)
    if (len(df) == 0):
        return DF_NULL
    return _df_index(df)

def from_csv(r):
    df = pd.read_csv(r)
    return _df_index(df)

def from_csvs(iolist):
    return pd.concat([ from_csv(i) for i in iolist ])

def gini(x):
    # Mean absolute difference
    mad = np.abs(np.subtract.outer(x, x)).mean()
    # Relative mean absolute difference
    rmad = mad/np.mean(x)
    # Gini coefficient
    return 0.5 * rmad

def lorenz(v):
    x = np.linspace(0., 100., 21)
    total = float(np.sum(v))
    y = []
    for xi in x:
        yi_vals = v[v <= np.percentile(v, xi)]
        yi = (np.sum(yi_vals) / total) * 100.0
        y.append(yi)
    return x, y

def _ts_to_string(ts):
    pattern = r"(\d+)([a-zA-Z])"
    r = re.match(pattern,ts)
    (r.group(1),r.group(2))
    MAP = dict(W="Weeks",D="Days",M="Months",Y="Years")
    unit = MAP[r.group(2).upper()]
    count = r.group(1)
    return f"{count} {unit}"


def _in_sprint(df, timeslot="2W"):
    df_resampled = df.resample(timeslot).sum()
    df_resampled["team"] = df["author"].resample(timeslot).nunique()
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
    plt.fill_between(bins,bins,result,color="blue",alpha=0.2)
    plt.fill_between(bins,result,color="red",alpha=0.2)
    title_label = f"GINI COEFFICIENT: {gi:.1%}"
    plt.title(title_label,fontsize=TITLE_SIZE)
    plt.legend()
    pass

def _plot_hist(df, plt,ts):
    v = df.lines.values
    timeslot = _ts_to_string(ts)
    plt.hist(v, bins=50)
    plt.title(f"Histgram of Lines of Code in {timeslot}", fontsize=TITLE_SIZE)

    plt.xlabel(f"Total Change in {timeslot}")
    plt.ylabel("Count")


def _plot_team(df, plt):
    date = df.index.values   
    team = df["team"]
    mean = team.mean()
    plt.title( f"Efficient Team Members  :{mean :.1f}" ,fontsize=TITLE_SIZE)
    plt.plot(date,team,marker=".",label="commit authors")
    plt.plot(date, np.ones(len(team)) * mean, "--", label="mean")
    plt.xlim(date[0], date[-1])
    plt.ylabel("Unique number of committed author")
    plt.legend()

def _plot_code(df, plt):
    date = df.index.values
    total_change = df.lines.sum()
    total_added = (df.insertions - df.deletions).sum()
    plt.title(f"Code Output : change={total_change:,d},added={total_added:,d},",fontsize=TITLE_SIZE)
    plt.plot(date,df.lines,label="lines")
    plt.plot(date,df.insertions,color="g",label="insertions")
    plt.plot(date,df.deletions, color="r", label="deletions")
    plt.xlim(date[0], date[-1])
    plt.ylabel("Lines")
    plt.fill_between(date,df.insertions,df.deletions,where = df.insertions >= df.deletions,color="g",alpha=0.5,interpolate=True)
    plt.fill_between(date,df.insertions,df.deletions,where = df.insertions < df.deletions,color="r",alpha=0.5,interpolate=True)
    plt.legend()

def plot(df, timeslot='2W', output=False, name="[This Graph]"):
    suptitle =  f"{name} : created by 'gilot'"
    
    dfs = _in_sprint(df,timeslot =timeslot)
    plt.figure(figsize=(16, 9))
    plt.tight_layout(pad = 0.05,w_pad=0)
    plt.suptitle(suptitle, fontsize=13,y=0.95,x=0.8)
    plt.subplots_adjust(wspace=0.15, hspace=0.4)
    # PLOT GINI / LORENTZ
    plt.subplot(2, 2, 1)
    _plot_gini(dfs,plt)

    # PlOT HIST
    plt.subplot(2, 2, 3)
    _plot_hist(dfs,plt,timeslot)

    # PLOT CODE
    plt.subplot(2, 2, 2)
    _plot_code(dfs,plt)

    # PLOT TEAM
    plt.subplot(2, 2, 4)
    _plot_team(dfs,plt)
    if(output) :
        plt.savefig(output,dpi = 150,bbox_inches='tight')
        
    else:
        plt.show()

