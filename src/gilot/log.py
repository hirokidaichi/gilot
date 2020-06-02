

import git
import datetime
import pandas as pd

from dateutil.relativedelta import relativedelta

DF_NULL = pd.DataFrame(
    [],
    columns=[
        "date",
        "hexsha",
        "author",
        "insertions",
        "deletions",
        "lines",
        "files"])
DF_NULL.set_index("date", inplace=True)


def dateformat(date):
    return datetime.datetime.fromtimestamp(date).strftime("%Y-%m-%d %H:%M:%S")


def commit_to_dict(commit):
    # TODO 拡張子ごとにフィルタできたりしたほうがYAMLの編集とか入らないからいいだろうか。
    return dict(
        date=dateformat(
            commit.committed_date),
        hexsha=commit.hexsha,
        author=commit.author.name,
        **commit.stats.total)


def log(
        repo,
        branch="origin/HEAD",
        since=datetime.date.today() - relativedelta(months=6)):
    return [commit_to_dict(c) for c in repo.iter_commits(branch, since=since)]


def _df_index(df):
    df.date = pd.to_datetime(df.date)
    df.set_index("date", inplace=True)
    df.sort_index()
    return df


def from_repo(r, **kwargs):
    logs = log(r, **kwargs)
    df = pd.DataFrame.from_records(logs)
    if (len(df) == 0):
        return DF_NULL
    return _df_index(df)


def from_dir(r, **kwargs):
    return from_repo(git.Repo(r), **kwargs)


def from_csv(r):
    df = pd.read_csv(r)
    return _df_index(df)


def from_csvs(iolist):
    return pd.concat([from_csv(i) for i in iolist])
