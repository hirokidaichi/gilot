
import argparse
import json
import logging
import sys
from fnmatch import fnmatch
from logging import getLogger
from typing import Callable, List, Optional

import gilot
from gilot.core import Duration
logger = getLogger(__name__)

parser = argparse.ArgumentParser(description="""
gilot is a tool for analyzing and visualizing git logs

1) simple way (1 liner using pipe)
! gilot log REPO_DIR | gilot plot

2) 2-phase way
! gilot log REPO_DIR > repo.csv
! gilot plot -i repo.csv -o graph.png


""", formatter_class=argparse.RawDescriptionHelpFormatter)  # type:ignore


def init_logger(args):
    root_logger = logging.getLogger()
    log_level = max(logging.NOTSET,logging.WARNING - args.verbose * 10)
    root_logger.setLevel(logging.NOTSET)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    root_logger.addHandler(handler)


def add_logging_option(parser):
    parser.add_argument("-v","--verbose",action="count",default=0,help="increase log level")


def compose_filter(allow: Optional[List[str]], deny: Optional[List[str]]) -> Callable[[str], bool]:
    allow_list = allow or ["*"]
    deny_list = deny or []

    def match(file_name: str) -> bool:
        # いずれかのallow条件にmatchするか
        is_allowed = any(fnmatch(file_name, p) for p in allow_list)
        # いずれかのdeny条件にmatchするか
        is_denyed = any(fnmatch(file_name, p) for p in deny_list)
        # 許可されており、拒否リストに含まれていない。
        return (is_allowed and not is_denyed)

    return match


def args_to_duration(args) -> Duration:

    if (args.since and args.until):
        return Duration.range(args.since, args.until)
    if (args.since and args.month):
        return Duration.months(int(args.month),since=args.since)
    if (args.since):
        return Duration.months(6,since=args.since)
    if (args.month):
        return Duration.months(int(args.month))
    return Duration.months(6)


def handle_log(args) -> None:
    init_logger(args)
    duration = args_to_duration(args)
    df = gilot.from_dir(
        args.repo,
        branch=args.branch,
        duration=duration,
        full=args.full
    )
    df.to_csv(args.output)


def handle_plot(args) -> None:
    init_logger(args)
    df = gilot.from_csvs(args.input)
    if (args.allow_files or args.ignore_files):
        df = df.filter_files(compose_filter(allow=args.allow_files,deny=args.ignore_files))
    gilot.plot(df, output=args.output, name=args.name, timeslot=args.timeslot)


def handle_info(args) -> None:
    init_logger(args)
    df = gilot.from_csvs(args.input)
    if (args.allow_files or args.ignore_files):
        df = df.filter_files(compose_filter(allow=args.allow_files,deny=args.ignore_files))

    print(json.dumps(gilot.info(df), indent=4, sort_keys=False))


def handle_hotspot(args) -> None:
    init_logger(args)
    df = gilot.from_csvs(args.input)
    result = gilot.hotspot(
        df.expand_files(
            compose_filter(
                allow=args.allow_files,
                deny=args.ignore_files)))
    if(args.csv) :
        result.to_csv(args.output)
    else :
        pretty_print_hotspot(result[:args.num])


def handle_author(args) -> None:
    init_logger(args)
    df = gilot.from_csvs(args.input)
    if (args.allow_files or args.ignore_files):
        df = df.filter_files(compose_filter(allow=args.allow_files,deny=args.ignore_files))

    gilot.authors(df, output=args.output, name=args.name,top=args.top,only=args.only)


def handle_hotgraph(args) -> None:
    init_logger(args)
    df = gilot.from_csvs(args.input)
    is_match = compose_filter(allow=args.allow_files,deny=args.ignore_files)
    epanded_df = df.expand_files(is_match)
    gilot.hotgraph(
        epanded_df,
        output_file_name=args.output,
        rank=args.rank,
        stop_retry=args.stop_retry)


def pretty_print_hotspot(df) -> None:
    print("""
------------------------------------------------------------
    gilot hotspot ( https://github.com/hirokidaichi/gilot )
------------------------------------------------------------
    """)
    targets = ["hotspot","commits","authors","file_name"]
    columns_text = " ".join([f"{t:>8}" for t in targets])
    print(columns_text)
    for k,v in df.iterrows():

        hotspot = "{:.2f}".format(v["hotspot"])
        commits = "{:6d}".format(int(v["commits"]))
        authors = "{:6d}".format(int(v["authors"]))
        row = [hotspot,commits,authors,k]
        print(" ".join([f"{c:>8}" for c in row]))


def add_file_filter_option(parser):
    parser.add_argument(
        "--allow-files",
        nargs="*",
        help="""
        Specify the files to allow.
        You can specify more than one like 'src/*' '*.rb'. Only data with the --full flag is valid.""")

    parser.add_argument(
        "--ignore-files",
        nargs="*",
        help="""
        Specifies files to ignore.
        You can specify more than one like 'dist/*' '*.gen.java'. Only data with the --full flag is valid.""")


def add_author_filter_option(parser):
    parser.add_argument(
        "--allow-authors",
        nargs="*",
        help="""
        Specify the files to allow.
        You can specify more than one like 'src/*' '*.rb'. Only data with the --full flag is valid.""")

    parser.add_argument(
        "--ignore-authors",
        nargs="*",
        help="""
        Specifies files to ignore.
        You can specify more than one like 'dist/*' '*.gen.java'. Only data with the --full flag is valid.""")


def add_log_option(parser):
    """
        gilot log コマンドのオプション
    """
    parser.add_argument(
        'repo',
        help='REPO must be a root dir of git repository')

    parser.add_argument(
        "-b", "--branch",
        help="target branch name. default 'origin/HEAD' ",
        default="origin/HEAD")

    parser.add_argument(
        "-o", "--output",
        default=sys.__stdout__)

    parser.add_argument(
        "--since",
        help="SINCE must be ISO format like 2020-01-01.")

    parser.add_argument(
        "--until",
        help="UNTIL must be ISO format like 2020-06-01.")

    parser.add_argument(
        "--month",
        help="MONTH is how many months of log data to output. default is 6")

    parser.add_argument(
        "--full",
        action="store_true",
        help="If this flag is enabled, detailed data including the commuted file name will be output.")

    parser.set_defaults(handler=handle_log)
    return parser


def add_plot_option(parser):
    """
        gilot plot コマンドのオプション
    """
    parser.add_argument(
        '-i', "--input",
        nargs="*",
        default=[sys.__stdin__])

    parser.add_argument(
        '-t', "--timeslot",
        help="resample period like 2W or 7D or 1M ",
        default="2W")

    parser.add_argument(
        '-o', "--output",
        default=False,
        help="OUTPUT FILE ")

    parser.add_argument(
        "-n", "--name",
        default="GIT LOG REPORT",
        help="name")

    add_file_filter_option(parser)
    parser.set_defaults(handler=handle_plot)
    return parser


def add_info_option(parser):
    """
        gilot info コマンドのオプション
    """
    parser.add_argument(
        '-i', "--input",
        nargs="*",
        default=[sys.__stdin__])

    parser.add_argument(
        '-t', "--timeslot",
        help="resample period like 2W or 7D or 1M ",
        default="2W")

    add_file_filter_option(parser)

    parser.set_defaults(handler=handle_info)
    return parser


def add_hotspot_option(parser):
    """
        gilot hotspot コマンドのオプション
    """
    parser.add_argument(
        '-i', "--input",
        nargs="*",
        default=[sys.__stdin__])

    parser.add_argument(
        '-n', "--num",
        type=int,
        default=30)

    parser.add_argument(
        "--csv",
        action="store_true",
        help="dump csv")

    parser.add_argument(
        "-o", "--output",
        default=sys.__stdout__)

    add_file_filter_option(parser)

    parser.set_defaults(handler=handle_hotspot)
    return parser


def add_hotgraph_option(parser):
    """
        gilot hotgraph コマンドのオプション
    """
    parser.add_argument(
        '-i', "--input",
        nargs="*",
        default=[sys.__stdin__])

    parser.add_argument(
        '-r', "--rank",
        type=int,
        default=70)

    # 10秒以上かかる処理だった場合に自動的に閾値を引き上げてリトライする。
    parser.add_argument(
        "--stop-retry",
        action="store_true")

    parser.add_argument(
        "--csv",
        action="store_true",
        help="dump csv")

    parser.add_argument(
        "-o", "--output",
        default=False)

    add_file_filter_option(parser)

    parser.set_defaults(handler=handle_hotgraph)
    return parser


def add_author_option(parser):
    """
        gilot authors コマンドのオプション
    """
    parser.add_argument(
        '-i', "--input",
        nargs="*",
        default=[sys.__stdin__])

    parser.add_argument(
        '-o', "--output",
        default=False,
        help="OUTPUT FILE ")

    parser.add_argument(
        '-t', "--top",
        type=int,
        default=10)

    parser.add_argument(
        '-n',"--name",
        default="--",
        help="name")

    parser.add_argument(
        "--only",
        nargs="*")

    add_file_filter_option(parser)

    parser.set_defaults(handler=handle_author)
    return parser


"""
    gilot コマンドのオプション
"""

subparsers = parser.add_subparsers()


subparsers_list = [
    add_log_option(subparsers.add_parser(
        'log', help='make git log csv data/ see `log -h`')),
    add_plot_option(subparsers.add_parser(
        'plot', help='plot graph using the csv file see `plot -h`')),
    add_info_option(subparsers.add_parser(
        'info', help='info graph using the csv file see `info -h`')),
    add_hotspot_option(subparsers.add_parser(
        'hotspot', help='search hotpost files `hotspot -h`')),
    add_hotgraph_option(subparsers.add_parser(
        'hotgraph', help='plot hotpost network `hotgraph -h`')),
    add_author_option(subparsers.add_parser(
        'author', help='author hotpost network `author -h`')),
]

for p in subparsers_list:
    add_logging_option(p)


def main():
    # コマンドライン引数をパースして対応するハンドラ関数を実行
    args = parser.parse_args()
    if hasattr(args, 'handler'):
        args.handler(args)
    else:
        # 未知のサブコマンドの場合はヘルプを表示
        parser.print_help()


if __name__ == "__main__":
    main()
