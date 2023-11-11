C_PROGRAM = """
#include "common.h"
#include "bpf_helpers.h"

#include <stddef.h>

char __license[] SEC("license") = "Dual MIT/GPL";

struct {{
    __uint(type, BPF_MAP_TYPE_RINGBUF);
	__uint(max_entries, 1 << 24);
}} events SEC(".maps");

struct event{{
    int syscall_number;
}};

const struct event *unused_event __attribute__((unused));


{structs}
{functions}
"""

C_FUNCTION_TEMPLATE = """
SEC("tracepoint/syscalls/{function_name}")
int {function_name}(struct {struct_name}* ctx){{
    struct event* event;
    event = bpf_ringbuf_reserve(&events, sizeof(struct event), 0);
    if(event == 0){{
        return -1;
    }}
    event->syscall_number = ctx->__syscall_nr;
    bpf_ringbuf_submit(event, 0);
    return 0;
}}"""

C_STRUCT_TEMPLATE = "struct {struct_name}\n{{\n{params}}};\n"

GO_PROGRAM = """
package main

import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"unsafe"

	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
	"github.com/cilium/ebpf/rlimit"
)

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -cc $BPF_CLANG -cflags $BPF_CFLAGS -type event bpf main.c -- -I/home/user/ebpf/examples/headers
var objs = bpfObjects{{}}

func main() {{
	stopper := make(chan os.Signal, 1)
	signal.Notify(stopper, os.Interrupt, syscall.SIGTERM)

	if err := rlimit.RemoveMemlock(); err != nil {{
		log.Fatal(err)
	}}

	if err := loadBpfObjects(&objs, nil); err != nil {{
		panic(err)
	}}
	defer objs.Close()
	link, err := link.Tracepoint("syscalls", "{syscall_name}", objs.{uppercase_syscall_name}, nil)
	if err != nil {{
		panic("error")
	}}
	defer link.Close()

	rd, err := ringbuf.NewReader(objs.bpfMaps.Events)
	go readLoop(rd)

	<-stopper
}}

const __sz_event = unsafe.Sizeof(bpfEvent{{}})

func (e *bpfEvent) UnmarshalBinary(b []byte) {{
	if len(b) != int(__sz_event) {{
		log.Fatalf("expected %d got %d", __sz_event, len(b))
		return
	}}
	*e = *(*bpfEvent)(unsafe.Pointer(&b[0]))
}}

func readLoop(rd *ringbuf.Reader) {{
	var event bpfEvent
	for {{
		record, err := rd.Read()
		if err != nil {{
			panic(err)
		}}

		event.UnmarshalBinary(record.RawSample)
		fmt.Println(event.SyscallNumber)
	}}
}}

"""


class Parameter:
    def __init__(self, data_type, name):
        self.__data_type = data_type
        self.__name = name

    def dump(self):
        s = "data_type = " + str(self.__data_type) + "; name = " + self.__name
        return s

    def make_param(self):
        return self.__data_type + " " + self.__name


def convert_to_uppercase(name):
    s = ""

    words = name.split('_')
    for word in words:
        s += word.capitalize()

    return s


class Program:
    def __init__(self):
        self.__name = ""
        self.__parameters = []

    def set_name(self, name):
        self.__name = name

    def dump_program(self):
        s = ""
        s += "name: " + self.__name

        for parameter in self.__parameters:
            s += parameter.dump()

        return s

    def set_parameters(self, parameters):
        self.__parameters = parameters

    def make_params_struct_name(self):
        return self.__name + "_params"

    def make_struct(self):
        params = ""
        for param in self.__parameters:
            params += "     " + param.make_param() + ";" + "\n"

        s = C_STRUCT_TEMPLATE.format(
            struct_name=self.make_params_struct_name(),
            params=params
        )
        return s

    def make_program_c_code(self):
        structs = self.make_struct()

        function = C_FUNCTION_TEMPLATE.format(
            function_name=self.__name,
            struct_name=self.make_params_struct_name()
        )

        s = C_PROGRAM.format(
            structs=structs,
            functions=function
        )

        return s

    def make_program_go_code(self):
        s = GO_PROGRAM.format(
            syscall_name=self.__name,
            uppercase_syscall_name=convert_to_uppercase(self.__name)
        )

        return s
