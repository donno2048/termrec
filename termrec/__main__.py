from . import main_play, main_rec
from argparse import ArgumentParser
from questionary import path
from tty import setraw
from termios import tcgetattr, tcsetattr
def parse(rec = False):
    parser, article = ArgumentParser(description = "Record your terminal and play it using `termrec` and `termplay`"), 'a' if rec else 'the'
    group = parser.add_mutually_exclusive_group(required = True)
    group.add_argument('-p', '--path', type = str, help = f"Give {article} path for {article} file {'to save the recording to' if rec else 'you want to play'}")
    group.add_argument('-P', '--path-prompt', action='store_true', help = f"Give {article} path for {article} file {'to save the recording to' if rec else 'you want to play'} using a prompt")
    if rec: parser.add_argument('-c', '--command', metavar='', type = str, help = "Give a custom command to record")
    return parser.parse_args()
def parse_rec():
    args = parse(True)
    main_rec(args.path, args.command)
def parse_play():
    old_set = tcgetattr(0)
    try:
        setraw(0)
        args = parse()
        main_play(args.path if not args.path_prompt else path('Path to recording').ask())
    finally: tcsetattr(0, 1, old_set)
