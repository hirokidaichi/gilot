from __future__ import annotations

import git
import datetime
import json
import pandas as pd
from typing import Type,List,Optional,Callable
from dataclasses import dataclass,asdict,fields
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

    def __str__(self) -> str:
        return f"({self.since_text()} - {self.until_text()})"

    def until_text(self) -> str:
        if (self.until):
            return date_to_text(self.until)
        return "now"

    def delta(self) -> datetime.timedelta:
        if(self.until and self.since):
            return self.until - self.since
        return (datetime.date.today()) - self.since

    @classmethod
    def months(cls:Type[Duration], months: int,*,since:Optional[str] = None) -> Duration:
        if(since is None):
            # 今からnヶ月前　から　今　までの期間
            delta = relativedelta(months=-int(months))
            return cls(until=None,since=datetime.date.today() + delta)
        # 指定時刻からnヶ月間
        delta = relativedelta(months=int(months))
        since_date = text_to_date(since)
        until = since_date + delta

        return cls(until=until,since=since_date)

    @classmethod
    def range(cls:Type[Duration],since: str, until: str) -> Duration:
        return cls(since=text_to_date(since),until=text_to_date(until))

    @classmethod
    def from_now(cls: Type[Duration], since_text: str) -> Duration:
        since = text_to_date(since_text)
        return cls(until=None,since=since)


DEFAULT_DURATION = Duration.months(6)


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
    files_json : Optional[str]

    @ classmethod
    def compose(cls, commit: git.Commit,full : bool = False) -> CommitRecord:
        total = commit.stats.total
        file_json = json.dumps(commit.stats.files) if(full) else None

        return cls(
            date=timestamp_to_date_text(commit.committed_date),
            hexsha=commit.hexsha,
            author=commit.author.name,
            insertions=total["insertions"],
            deletions=total["deletions"],
            lines=total["lines"],
            files=total["files"],
            files_json=file_json
        )

    def to_dict(self) -> dict:
        return asdict(self)

    def filter_files(self,is_match_file:Callable[[str],bool]) -> CommitRecord:
        if (not self.files_json):
            return self

        file_info = json.loads(self.files_json)
        insertions = 0
        deletions = 0
        lines = 0
        files = 0

        for k,v in file_info.items():
            if (is_match_file(str(k))):
                insertions += v["insertions"]
                deletions += v["deletions"]
                lines += v["lines"]
                files += 1

        self.insertions = insertions
        self.deletions = deletions
        self.lines = lines
        self.files = files
        self.files_json = None
        return self


class CommitDataFrame(pd.DataFrame):
    DF_NULL = pd.DataFrame([],columns=[i.name for i in fields(CommitRecord)])
    DF_NULL.set_index("date", inplace=True)

    @ classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> CommitDataFrame:
        if (len(df) == 0):
            return cls.DF_NULL
        df.date = pd.to_datetime(df.date)
        df.set_index("date", inplace=True)
        df.sort_index()
        return df

    @classmethod
    def from_records(cls, commits: List[CommitRecord]) -> CommitDataFrame:
        return cls.from_dataframe(pd.DataFrame.from_records(
            [commit.to_dict() for commit in commits]))

    @ classmethod
    def from_commits(cls,commits: List[git.Commit],*,full:bool = False) -> CommitDataFrame:
        return cls.from_records(
            [CommitRecord.compose(c, full=full) for c in commits])


def from_csv(csvFileName: str) -> CommitDataFrame:
    df:pd.DataFrame = pd.read_csv(csvFileName)
    return CommitDataFrame.from_dataframe(df)


def from_csvs(csvFileNames: List[str]) -> CommitDataFrame:
    return pd.concat([from_csv(i) for i in csvFileNames])


def filter_files(df: CommitDataFrame, file_name_filter:Callable[[str],bool]) -> CommitDataFrame:

    def convert(index, row):
        cr = CommitRecord(date=str(index),**row.to_dict())
        return cr.filter_files(file_name_filter)

    return CommitDataFrame.from_records([convert(index,row) for index,row in df.iterrows()])


def from_dir(
    dirName: str = "./",*,
    branch: str = "origin/HEAD",
    duration: Duration = DEFAULT_DURATION,
    full : bool = False,


) :
    commits = Repo.from_dir(dirName, branch=branch).commits(duration)
    return CommitDataFrame.from_commits(commits,full=full)
