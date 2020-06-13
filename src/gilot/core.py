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
        since_text = self.since_text()
        until_text = self.until_text()
        return f"({since_text} - {until_text})"

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

    def expand(self) -> List[dict]:
        if (not self.files_json):
            return [self.to_dict()]

        date = self.date
        hexsha = self.hexsha
        author = self.author
        file_info = json.loads(self.files_json)

        return [dict(date=date,hexsha=hexsha,author=author,file_name=str(k),**v)
                for k,v in file_info.items()]

    def filter_files(self,is_match_file:Callable[[str],bool]) -> Optional[CommitRecord]:
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

        if(files == 0) :
            return None

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
        return cls.up(df)

    @classmethod
    def up(cls, df: pd.DataFrame) -> CommitDataFrame:
        return cls(df.to_numpy(),index=df.index,columns=df.columns)

    @classmethod
    def from_records(cls, commits: List[CommitRecord]) -> CommitDataFrame:
        return cls.from_dataframe(pd.DataFrame.from_records(
            [commit.to_dict() for commit in commits if commit is not None]))

    @ classmethod
    def from_commits(cls,commits: List[git.Commit],*,full:bool = False) -> CommitDataFrame:
        return cls.from_records(
            [CommitRecord.compose(c, full=full) for c in commits])

    def filter_files(self,is_match : Callable[[str],bool]) -> CommitDataFrame:
        records = [cr.filter_files(is_match) for cr in self.to_records()]
        filtered = [r for r in records if r is not None]

        return CommitDataFrame.from_records(filtered)

    def to_records(self) -> List[CommitRecord]:
        def convert(index, row):
            return CommitRecord(date=str(index),**row.to_dict())
        return [convert(index,row) for index,row in self.iterrows()]

    def expand_files(self,is_match:Callable[[str],bool]) -> pd.DataFrame:
        dics = [e for c in self.to_records()
                for e in c.expand()
                if is_match(e["file_name"])]
        df = pd.DataFrame.from_records(dics)
        df.date = pd.to_datetime(df.date)
        df.set_index("date",inplace=True)
        df.sort_index()
        return df


def from_csv(csvFileName: str) -> CommitDataFrame:
    return CommitDataFrame.from_dataframe(pd.read_csv(csvFileName))


def from_csvs(csvFileNames: List[str]) -> CommitDataFrame:
    return CommitDataFrame.up(pd.concat([from_csv(i) for i in csvFileNames]))


def from_dir(
        dirName: str = "./",*,
        branch: str = "origin/HEAD",
        duration: Duration = DEFAULT_DURATION,
        full : bool = False) :
    commits = Repo.from_dir(dirName, branch=branch).commits(duration)
    return CommitDataFrame.from_commits(commits,full=full)
