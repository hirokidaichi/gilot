import gilot.core
import pytest
import os
import shutil
from fnmatch import fnmatch
from gilot.core import Duration


@pytest.fixture
def tempdir():
    os.makedirs("./temp/", exist_ok=True)
    yield
    shutil.rmtree("./temp/")


def echo(p):
    assert isinstance(p,Duration)
    return p


def test_duration_constructor():
    assert echo(Duration.range("2012-10-10", "2020-10-10"))
    assert echo(Duration.months(5))


def test_commit_record(tempdir):
    df = gilot.core.from_dir("./")
    assert isinstance(df, gilot.core.CommitDataFrame) ,"i"
    df.to_csv("./temp/self.csv")
    csv_df = gilot.core.from_csv("./temp/self.csv")
    assert isinstance(csv_df, gilot.core.CommitDataFrame)
    df.to_csv("./temp/self2.csv")
    csv_df2 = gilot.core.from_csvs(["./temp/self.csv","./temp/self2.csv"])
    assert isinstance(csv_df2, gilot.core.CommitDataFrame)
    assert(len(csv_df2["hexsha"].value_counts()) == len(csv_df2))


def test_expander():
    df = gilot.core.from_dir("./", full=True, duration=Duration.months(60))
    import json
    for v in df["files_json"].values:
        obj = json.loads(str(v))
        assert isinstance(obj, dict)

    edf = df.expand_files()

    assert (len(edf["file_name"]) > 0)


def test_expander_with_filter():
    def is_match(file_name):
        return fnmatch(file_name,"*app.py")
    df = gilot.core.from_dir("./", full=True, duration=Duration.months(60))
    import json
    for v in df["files_json"].values:
        assert isinstance(json.loads(str(v)),dict)

    edf = df.expand_files(is_match)
    odf = df.expand_files()

    assert (len(edf["file_name"]) > 0)
    assert (len(odf["file_name"]) > 0)
    assert (len(odf["file_name"]) > len(edf["file_name"]))
