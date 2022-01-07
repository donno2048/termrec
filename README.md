# termrec

Record your terminal and play it

## install

### From PyPI

`pip3 install pytermrec`

### From GitHub

`pip3 install git+https://github.com/donno2048/termrec`

## Usage

Just type the command in the terminal:

### Record to a file

```sh
termrec -p <filepath> # record without default command
termrec -p <filepath> -c <command to record> # record with custom command
```

To stop recording use the `exit` command or just <kbd>ctrl</kbd> + <kbd>D</kbs>

### Play a file

```sh
termplay -p <filepath>
# or with a prompt
termplay -P
```
