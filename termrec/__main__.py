from . import main_play, main_rec
from argparse import ArgumentParser
from tty import setraw
from termios import tcgetattr, tcsetattr
def parse(rec = False):
    parser, article = ArgumentParser(description = "Record your terminal and play it using `termrec` and `termplay`"), 'a' if rec else 'the'
    parser.add_argument('-p', '--path', required = True, type = str, help = f"Give {article} path for {article} file {'to save the recording to' if rec else 'you want to play'}")
    if rec: parser.add_argument('-c', '--command', metavar='', type = str, help = "Give a custom command to record")
    return parser.parse_args()
def parse_rec():
    args = parse(True)
    main_rec(args.path, args.command)
def parse_play():
    old_set = tcgetattr(0)
    try:
        setraw(0)
        main_play(parse().path)
    finally: tcsetattr(0, 1, old_set)