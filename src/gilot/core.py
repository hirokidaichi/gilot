
from __future__ import annotations

import git
import datetime
import pandas as pd
from typing import Type,List,Optional
from dataclasses import dataclass,asdict
from dateutil.relativedelta import relativedelta


def text_to_date(date_text:str) -> datetime.date:
    return datetime.date.fromisoformat(date_text)


def date_to_text(date: datetime.date) -> str:
    return date.isoformat()


@dataclass
class Duration:

    since: datetime.date
    until: Optional[datetime.date]

    def to_dict(self) -> dict:
        return dict(since=self.since,until=self.until)

    def since_text(self) -> str:
        return date_to_text(self.since)

    def until_text(self) -> str:
        if (self.until):
            return date_to_text(self.until)
        return "now"

    def delta(self) -> datetime.timedelta:
        return (self.until or datetime.datetime.now()) - self.since

    @classmethod
    def months(cls:Type[Duration], months: int,*,since:Optional[str] = None) -> Duration:
        delta = relativedelta(months=-int(months))
        since_date = text_to_date(since) if(since) else datetime.date.today() + delta
        return cls(until=None,since=since_date)

    @classmethod
    def range(cls:Type[Duration],since: str, until: str) -> Duration:
        return cls(since=text_to_date(since),until=text_to_date(until))

    @classmethod
    def from_now(cls: Type[Duration], since_text: str) -> Duration:
        since = text_to_date(since_text)
        return cls(until=None,since=since)


DEFAULT_DURATION = Duration.months(6)

# def _type_date_period(months):


@dataclass
class Repo:
    repo: git.Repo
    branch : str

    @classmethod
    def from_dir(
            cls,
            repo_dir:str,
            branch: str) -> Repo:
        return cls(repo=git.Repo(repo_dir), branch=branch)

    def commits(self, duration: Duration) -> List[git.Commit]:
        return self.repo.iter_commits(
            self.branch,
            since=duration.since_text(),
            until=duration.until_text())


def timestamp_to_date_text(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


@ dataclass
class CommitRecord:
    date: str
    hexsha : str
    author : str
    insertions : int
    deletions :int
    lines:int
    files: int

    def to_dict(self) -> dict:
        return asdict(self)

    @ classmethod
    def from_commit(cls, commit: git.Commit) -> CommitRecord:
        total = commit.stats.total
        return cls(
            date=timestamp_to_date_text(commit.committed_date),
            hexsha=commit.hexsha,
            author=commit.author.name,
            insertions=total["insertions"],
            deletions=total["deletions"],
            lines=total["lines"],
            files=total["files"]
        )

    @classmethod
    def from_commits(cls, commits: List[git.Commit]) -> List[CommitRecord]:
        return [cls.from_commit(c) for c in commits]


class CommitDataFrame(pd.DataFrame):
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

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> CommitDataFrame:
        if (len(df) == 0):
            return cls.DF_NULL
        df.date = pd.to_datetime(df.date)
        df.set_index("date", inplace=True)
        df.sort_index()
        return df

    @classmethod
    def from_commits(cls, commits: List[CommitRecord]) -> CommitDataFrame:
        return cls.from_dataframe(pd.DataFrame.from_records([c.to_dict() for c in commits]))


def from_csv(csvFileName: str) -> CommitDataFrame:
    df:pd.DataFrame = pd.read_csv(csvFileName)
    return CommitDataFrame.from_dataframe(df)


def from_csvs(csvFileNames: List[str]) -> CommitDataFrame:
    return pd.concat([from_csv(i) for i in csvFileNames])


@dataclass
class LoggerOption:
    branch: str


def from_dir(
    dirName: str = "./",*,
    branch: str = "origin/HEAD",
    duration: Duration = DEFAULT_DURATION,
) :
    commits = Repo.from_dir(dirName, branch=branch).commits(duration)
    return CommitDataFrame.from_commits(CommitRecord.from_commits(commits))
