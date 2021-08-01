from json import loads, dumps
from codecs import getincrementaldecoder
from time import time
from select import select
from os import read, environ, get_terminal_size, isatty, write, execvpe, pipe, O_NONBLOCK, waitpid, close
from array import array
from fcntl import ioctl, fcntl, F_GETFL, F_SETFL
from signal import signal, SIGCHLD, SIGHUP, SIGTERM, SIGQUIT, set_wakeup_fd, SIGWINCH
from termios import error, TCSAFLUSH, tcgetattr, tcsetattr, TIOCGWINSZ, TIOCSWINSZ
from multiprocessing import Process, Queue
WIDTH, HEIGHT = get_terminal_size()
ENV = {'SHELL': environ.get('SHELL'), 'TERM': environ.get('TERM')}
class writer():
    def __init__(self, path, header): self.path, self.decstdin, self.decstdout, self.header = path, getincrementaldecoder('UTF-8')('replace'), getincrementaldecoder('UTF-8')('replace'), header
    def __enter__(self):
        self.file = open(self.path, mode='w', buffering=1)
        self.write_line(self.header)
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback): self.file.close()
    def write_event(self, ts):
        ts, etype, data = ts
        ts = round(ts, 6)
        if etype == 'o':
            if type(data) == str: data = data.encode(encoding='utf-8', errors='strict')
            self.write_line([ts, etype, self.decstdout.decode(data)])
        elif etype == 'i':
            if type(data) == str: data = data.encode(encoding='utf-8', errors='strict')
            self.write_line([ts, etype, self.decstdin.decode(data)])
        else: self.write_line([ts, etype, data])
    def write_stdout(self, ts, data): self.write_event(ts, 'o', data)
    def write_stdin(self, ts, data): self.write_event(ts, 'i', data)
    def write_line(self, obj): self.file.write(dumps(obj, ensure_ascii=False, indent=None, separators=(', ', ': ')) + '\n')
def write_json(path, header, queue):
    with writer(path, header) as w:
        for event in iter(queue.get, None): w.write_event(event)
class async_writer():
    def __init__(self, path, metadata): self.path, self.metadata, self.queue = path, metadata, Queue()
    def __enter__(self):
        self.process = Process(target=write_json, args=(self.path, self.metadata, self.queue))
        self.process.start()
        self.start_time = time()
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.queue.put(None)
        self.process.join()
    def write_stdin(self, data): self.queue.put([time() - self.start_time, 'i', data])
    def write_stdout(self, data): self.queue.put([time() - self.start_time, 'o', data])
class raw():
    def __init__(self, fd): self.fd, self.restore = fd, False
    def __enter__(self):
        try:
            self.mode = tcgetattr(self.fd)
            __import__("tty").setraw(self.fd)
            self.restore = True
        except error: pass
    def __exit__(self, type, value, traceback):
        if self.restore: tcsetattr(self.fd, TCSAFLUSH, self.mode)
def record(command, writer):
    master_fd = None
    def _set_pty_size():
        if isatty(1):
            buf = array('h', [0, 0, 0, 0])
            ioctl(1, TIOCGWINSZ, buf, True)
        else: buf = array('h', [24, 80, 0, 0])
        ioctl(master_fd, TIOCSWINSZ, buf)
    def _write_stdout(data): write(1, data)
    def _handle_master_read(data):
        writer.write_stdout(data)
        _write_stdout(data)
    def _write_master(data):
        while data: data = data[write(master_fd, data):]
    def _handle_stdin_read(data): _write_master(data) #;writer.write_stdin(data)
    def _signals(signal_list): return [(sig, signal(sig, handler)) for sig, handler in signal_list]
    def _copy(signal_fd):
        fds = [master_fd, 0, signal_fd]
        while True:
            try: rfds, wfds, xfds = select(fds, [], [])
            except OSError as e:
                if e.errno == 4: continue
            if master_fd in rfds:
                data = read(master_fd, 1024)
                if not data: fds.remove(master_fd)
                else: _handle_master_read(data)
            if 0 in rfds:
                data = read(0, 1024)
                if not data: fds.remove(0)
                else: _handle_stdin_read(data)
            if signal_fd in rfds:
                data = read(signal_fd, 1024)
                if data:
                    signals = __import__("struct").unpack('%uB' % len(data), data)
                    for sig in signals:
                        if sig in [SIGCHLD, SIGHUP, SIGTERM, SIGQUIT]:
                            close(master_fd)
                            return
                        elif sig == SIGWINCH: _set_pty_size()
    pid, master_fd = __import__("pty").fork()
    if not pid: execvpe(command[0], command, environ)
    pipe_r, pipe_w = pipe()
    flags = fcntl(pipe_w, F_SETFL, fcntl(pipe_w, F_GETFL, 0) | O_NONBLOCK)
    set_wakeup_fd(pipe_w)
    old_handlers = _signals(map(lambda s: (s, lambda signal, frame: None), [SIGWINCH, SIGCHLD, SIGHUP, SIGTERM, SIGQUIT]))
    _set_pty_size()
    with raw(0):
        try: _copy(pipe_r)
        except (IOError, OSError): pass
    _signals(old_handlers)
    waitpid(pid, 0)
class Cast:
    def __init__(self, f, header): self.version, self.__file, self.v2_header, self.idle_time_limit = 2, f, header, header.get('idle_time_limit')
    def events(self):
        for line in self.__file: yield loads(line)
    def stdout_events(self):
        for time, type, data in self.events():
            if type == 'o': yield [time, type, data]
def file2cast(header, f): return Cast(f, header)
class open_file():
    def __init__(self, first_line, file): self.first_line, self.file = first_line, file
    def __enter__(self): return file2cast(loads(self.first_line), self.file)
    def __exit__(self, exc_type, exc_value, exc_traceback): self.file.close()
class file():
    def __init__(self, path): self.path = path
    def __enter__(self):
        self.file = open(self.path, mode='rt', encoding='utf-8')
        self.context = open_file(self.file.readline(), self.file)
        return self.context.__enter__()
    def __exit__(self, exc_type, exc_value, exc_traceback): self.context.__exit__(exc_type, exc_value, exc_traceback)
def play(cast):
    try:
        std = open('/dev/tty')
        with raw(std.fileno()): stdin = std
    except Exception: stdin = None
    base_time, keyboard_interrupt, paused, pause_time, not_broke = time(), False, False, None, True
    for t, _type, text in cast.stdout_events():
        delay = t - (time() - base_time)
        while stdin and not keyboard_interrupt and delay > 0:
            if paused:
                while not_broke:
                    fi, not_broke = stdin.fileno(), False
                    terminal = read(fi, 1024) if fi in select([fi], [], [], 1000)[0] else b''
                    if 3 in terminal: keyboard_interrupt = True
                    elif 32 in terminal: paused, base_time = False, base_time + (time() - pause_time)
                    elif 46 in terminal:
                        delay, pause_time = 0, time()
                        base_time = pause_time - t
                    else: not_broke = True
            else:
                fi = stdin.fileno()
                terminal = read(fi, 1024) if fi in select([fi], [], [], delay)[0] else b''
                if not terminal: break
                elif 3 in terminal:
                    keyboard_interrupt = True
                    break
                elif 32 in terminal:
                    paused, pause_time = True, time()
                    delay += pause_time - t - base_time
        if keyboard_interrupt: break
        __import__("sys").stdout.write(text)
        __import__("sys").stdout.flush()
def main_rec(path, command = None):
    with async_writer(path, {'width': WIDTH, 'height': HEIGHT, 'timestamp': int(time()), 'env': ENV}) as w: record(['sh', '-c', command or environ.get('SHELL') or 'sh'], w)
def main_play(path):
    with file(path) as a: play(a)
