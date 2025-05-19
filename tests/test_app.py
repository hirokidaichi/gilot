import sys
import os
import shutil
import pytest
from gilot.app import parser,args_to_duration
import json
import subprocess


@pytest.fixture
def tempdir():
    os.makedirs("./temp/", exist_ok=True)
    yield
    shutil.rmtree("./temp/")


def test_log_repo():
    a = parser.parse_args(["log","./"])
    assert a.repo == "./"


def test_log_branch():
    a = parser.parse_args(["log","./","-b","master"])
    assert a.repo == "./"
    assert a.branch == "master"
    b = parser.parse_args(["log","./","--branch","master"])
    assert b.repo == "./"
    assert b.branch == "master"
    c = parser.parse_args(["log","./"])
    assert c.repo == "./"
    assert c.branch == "origin/HEAD"


def test_log_output():
    a = parser.parse_args(["log","./","--output","target.file"])
    assert a.output == "target.file"
    b = parser.parse_args(["log","./"])
    assert b.output == sys.__stdout__


def test_log_duration():
    d = args_to_duration(parser.parse_args(["log","./"]))
    assert d.until_text() == "now"
    a = args_to_duration(parser.parse_args(
        ["log","./","--since","2019-01-20","--until","2020-01-20"]))
    assert a.since_text() == "2019-01-20"
    assert a.until_text() == "2020-01-20"

    b = args_to_duration(parser.parse_args(
        ["log","./","--since","2019-01-20","--month","10"]))
    assert b.since_text() == "2019-01-20"
    assert b.until_text() == "2019-11-20"

    c = args_to_duration(parser.parse_args(
        ["log","./","--month","10"]))
    assert c.until_text() == "now"

    d = args_to_duration(parser.parse_args(
        ["log","./","--since","2019-01-01","--month","10"]))
    assert d.since_text() == "2019-01-01"
    assert d.until_text() == "2019-11-01"

    d = args_to_duration(parser.parse_args(
        ["log","./","--since","2019-01-01"]))
    assert d.since_text() == "2019-01-01"
    assert d.until_text() == "2019-07-01"


def test_hotspot_option():
    a = parser.parse_args(["hotspot","--ignore-files","*.rb"])
    assert a.ignore_files == ["*.rb"]
    b = parser.parse_args(["hotspot","--allow-files","*.rb"])
    assert b.allow_files == ["*.rb"]
    c = parser.parse_args(["hotspot","-n","10","-i","input.csv"])
    assert c.num == 10
    assert c.input == ["input.csv"]


def test_handlers(tempdir):
    # log をえて、出力
    log = parser.parse_args(["log", "./", "--full", "--output", "temp/_test.csv", "--month", "60"])
    assert log.handler
    log.handler(log)
    plot = parser.parse_args(
        ["plot", "-i", "./temp/_test.csv", "--allow-files", "*.py", "--output", "temp/_test.png"])
    assert plot.handler

    plot.handler(plot)
    info = parser.parse_args(
        ["info", "-i", "./temp/_test.csv", "--allow-files", "*.py"])
    assert info.handler
    info.handler(info)

    hotspot = parser.parse_args(
        ["hotspot", "-i", "./temp/_test.csv", "--allow-files", "*.py"])
    assert hotspot.handler
    hotspot.handler(hotspot)

    hotspot2 = parser.parse_args(
        ["hotspot", "-i", "./temp/_test.csv", "--ignore-files", "*.lock","--csv"])
    assert hotspot2.handler
    hotspot2.handler(hotspot2)

    hotgraph = parser.parse_args(["hotgraph",
                                  "-i",
                                  "./temp/_test.csv",
                                  "--ignore-files",
                                  "*.lock",
                                  "--output",
                                  "./temp/hoge.png"])
    assert hotgraph.handler

    hotgraph.handler(hotgraph)
    hotgraph = parser.parse_args(["hotgraph",
                                  "-i",
                                  "./temp/_test.csv",
                                  "--ignore-files",
                                  "*.lock",
                                  "--rank","1",
                                  "--output",
                                  "./temp/hoge.png"])
    assert hotgraph.handler

    author = parser.parse_args(["author",
                                "-i",
                                "./temp/_test.csv",
                                "--ignore-files",
                                "*.lock",
                                "--top","1",
                                "--output",
                                "./temp/hoge.png"])
    assert author.handler
    author.handler(author)


def test_gilot_info_react_csv_matches_readme():
    # sample/react.csvをinputにgilot infoを実行
    csv_path = os.path.join(os.path.dirname(__file__), '../sample/react.csv')
    # gilot info -i sample/react.csv をサブプロセスで実行
    result = subprocess.run([
        sys.executable, '-m', 'gilot.app', 'info', '-i', csv_path
    ], capture_output=True, text=True)
    assert result.returncode == 0, f"gilot info failed: {result.stderr}"
    output = json.loads(result.stdout)

    # READMEの期待値
    expected = {
        "gini": 0.41398343573957913,
        "output": {
            "lines": 230004,
            "added": 66676,
            "refactor": 0.7101093894019235
        },
        "since": "2020-01-02 00:58:47",
        "until": "2020-06-19 10:18:56",
        "timeslot": "2 Weeks",
        "insertions": {
            "mean": 11410.76923076923,
            "std": 10912.175548088828,
            "min": 471.0,
            "25%": 3723.0,
            "50%": 7371.0,
            "75%": 17712.0,
            "max": 39681.0
        },
        "deletions": {
            "mean": 6281.846153846154,
            "std": 4380.664938989549,
            "min": 181.0,
            "25%": 3466.0,
            "50%": 5009.0,
            "75%": 9850.0,
            "max": 13477.0
        },
        "lines": {
            "mean": 17692.615384615383,
            "std": 14508.378898292196,
            "min": 652.0,
            "25%": 7369.0,
            "50%": 10780.0,
            "75%": 26834.0,
            "max": 52914.0
        },
        "files": {
            "mean": 361.61538461538464,
            "std": 262.79635286077144,
            "min": 35.0,
            "25%": 179.0,
            "50%": 359.0,
            "75%": 447.0,
            "max": 1062.0
        },
        "authors": {
            "mean": 13.615384615384615,
            "std": 4.8740548064635325,
            "min": 3.0,
            "25%": 10.0,
            "50%": 15.0,
            "75%": 16.0,
            "max": 21.0
        },
        "addedlines": {
            "mean": 5128.923076923077,
            "std": 8126.4102003030675,
            "min": -1337.0,
            "25%": -88.0,
            "50%": 2193.0,
            "75%": 6065.0,
            "max": 26448.0
        }
    }
    # 数値は小数点誤差を許容して比較
    def approx_equal(a, b, tol=1e-6):
        if isinstance(a, float) and isinstance(b, float):
            return abs(a - b) < tol
        return a == b

    def recursive_compare(d1, d2):
        assert d1.keys() == d2.keys(), f"Keys mismatch: {d1.keys()} vs {d2.keys()}"
        for k in d1:
            if isinstance(d1[k], dict):
                recursive_compare(d1[k], d2[k])
            else:
                assert approx_equal(d1[k], d2[k]), f"Mismatch at {k}: {d1[k]} vs {d2[k]}"

    recursive_compare(expected, output)
