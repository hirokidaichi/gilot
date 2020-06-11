
import datetime
import sys

from gilot.app import parser,args_to_duration


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
