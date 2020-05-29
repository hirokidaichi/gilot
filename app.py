import io
import sys
import glob
import datetime

import git
import argparse

import gilot
from dateutil.relativedelta import relativedelta

parser = argparse.ArgumentParser(description='''
gilot is a tool for analyzing and visualizing git change logs
''')


def handle_log(args):
    df = gilot.dataframe(args.repo, branch=args.branch, since=args.since or args.month)
    df.to_csv(args.output)

def handle_plot(args):
    df = gilot.from_csvs(args.input)
    gilot.plot(df,output=args.output,name=args.name)

def handle_info(args):
    df = gilot.from_csvs(args.input)
    
def handle_help(args):
    print(parser.parse_args([args.command, '--help']))


# str -> date 型変換関数
def _type_date(date_str):
    return datetime.date.fromisoformat(date_str)

def _type_date_period(months):
    delta = relativedelta(months=int(months))
    return datetime.date.today() - delta

def _type_repo(repo_dir):
    try :
        return git.Repo(repo_dir)
    except :
        print(f"repo:{repo_dir} must be git repogitry\n")
        parser.print_help()
        sys.exit(-1)

subparsers = parser.add_subparsers()

# log コマンドの parser を作成
parser_log = subparsers.add_parser('log', help=' see `log -h`')
parser_log.add_argument('repo',
    type=_type_repo,
    help='REPO must be a root dir of git repogitry')
parser_log.add_argument("-b", "--branch",
    default = "origin/HEAD"
)
parser_log.add_argument("-o","--output",
    help="output filename like --output hoge.csv",
    default=sys.__stdout__)
parser_log.add_argument("--since",
    help="DATE must be ISO format like 2020-01-01.",
    type=_type_date)
parser_log.add_argument("--month",
    help="MONTH is how many months of log data to output. default is 6",
    default = _type_date_period(6),
    type=_type_date_period)

parser_log.set_defaults(handler=handle_log)

# plot コマンドの parser を作成
parser_plot = subparsers.add_parser('plot', help='see `log -h`')
parser_plot.add_argument('-i', "--input",
    nargs="*",
    default=[sys.__stdin__])
parser_plot.add_argument('-o', "--output")
parser_plot.add_argument("-n", "--name",
    help="name")
parser_plot.set_defaults(handler=handle_plot)

# info コマンドの parser を作成
parser_info = subparsers.add_parser('info', help='see `log -h`')
parser_info.add_argument('-i', "--input",
    nargs="*",
    default= [sys.__stdin__])
parser_info.set_defaults(handler=handle_info)


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
