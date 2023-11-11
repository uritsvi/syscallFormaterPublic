import argparse
import dataclasses
import os.path
import subprocess

import Parser

MAKE_FILE_CODE = """
CLANG ?= clang-10
CFLAGS ?= -O2 -g -Wall -Werror

LIBEBPF_TOP = /home/user
EXAMPLES_HEADERS = $(LIBEBPF_TOP)/headers

all: generate

generate: export BPF_CLANG=$(CLANG)
generate: export BPF_CFLAGS=$(CFLAGS)
generate: export BPF_HEADERS=$(EXAMPLES_HEADERS)
generate:
	go generate main.go
"""

PATH = "/sys/kernel/debug/tracing/events/syscalls"
FORMAT_FILE_NAME = "format"

C_CODE_FILE_NAME = "main.c"
GO_CODE_FILE_NAME = "main.go"
MAKE_FILE_NAME = "Makefile"


@dataclasses.dataclass
class Command:
    syscall_name: str
    output_dir: str
    new_proj: bool


def pars_command():
    parser = argparse.ArgumentParser()
    parser.add_argument("tracepoint_name", type=str, help="tracepoint name")
    parser.add_argument("-o", "--output_dir", help="output directory")
    parser.add_argument('-new', '--new_project', help='clear all old files, create new project files', action='store_true')
    args = parser.parse_args()

    if args.output_dir is None:
        print("Output dir not specified!")

    command_object = Command(
        syscall_name=args.tracepoint_name,
        output_dir=args.output_dir,
        new_proj=args.new_project,
    )

    return command_object


def clear_all_files(directory):
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


def make_new_go_project(directory):
   os.system("bash -c 'cd {dir} && go mod init ebpfProj && go mod tidy'".format(dir=directory))


if __name__ == "__main__":
    command_obj = pars_command()

    print(command_obj)

    path = os.path.join(PATH, command_obj.syscall_name)
    path = os.path.join(path, FORMAT_FILE_NAME)

    text = None
    with open(path, "r") as syscall:
        text = syscall.readlines()

    final_text = ""
    for i in range(len(text) - 1):
        final_text += text[i]

    program = Parser.pars(final_text)

    c_code = program.make_program_c_code()
    go_code = program.make_program_go_code()

    print("c code:\n" + c_code)
    print("go code:\n" + go_code)

    c_code_path = os.path.join(command_obj.output_dir, C_CODE_FILE_NAME)
    go_code_path = os.path.join(command_obj.output_dir, GO_CODE_FILE_NAME)
    make_file_path = os.path.join(command_obj.output_dir, MAKE_FILE_NAME)

    if command_obj.new_proj:
        clear_all_files(command_obj.output_dir)
        make_new_go_project(command_obj.output_dir)

    with open(c_code_path, "w") as c_code_file:
        c_code_file.write(c_code)

    with open(go_code_path, "w") as go_code_file:
        go_code_file.write(go_code)

    with open(make_file_path, "w") as make_file:
        make_file.write(MAKE_FILE_CODE)

