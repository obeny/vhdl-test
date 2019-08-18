#!/usr/bin/env python3

import argparse
import glob
import os
import serial
import sys

import log

from enum import Enum
from enum import IntEnum

verbose=False
exec_name=os.path.realpath(sys.argv[0])

app_version = "0.7"
app_prog = os.path.splitext(os.path.basename(exec_name))[0]

app_description = "Executes generated test vectors on hardware simulator."
app_epilog = app_prog + " version: " + app_version + "\nCopyright (C) 2019 - Marcin 'obeny' Benka <obeny@obeny.net>\n\
This program may be freely redistributed under the terms of the GNU GPL v2"

#
# HELPERS
# =======
def intervalToNs(str):
	l = str.split(' ')
	value = int(l[0])
	mul = l[1]

	switcher = {
		"ns": 1,
		"us": 1000,
		"ms": 1000 * 1000,
		"s":  1000 * 1000 * 1000
	}
	return switcher.get(mul) * value

def clockToNs(str):
	l = str.split(' ')
	value = int(l[0])
	div = l[1]

	switcher = {
		"k": 1000,
		"M": 1000 * 1000,
	}

	if value == 0:
		return 100

	return (((1000 * 1000 * 1000) / switcher.get(div)) * 100) / value

def intervalStrToNs(str):
	mul = str[0]
	value = int(str[1:4])

	switcher = {
		"n": 1,
		"u": 1000,
		"m": 1000 * 1000,
		"s": 1000 * 1000 * 1000
	}
	return switcher.get(mul) * value

#
# ENUMS
# =====
class CommandType(IntEnum):
	RESET = 0
	SEND_REPORT = 1
	SET_META = 2
	SET_FLAGS = 3
	CFG_VECTOR = 4
	DEF_VECTOR = 5
	EXECUTE = 6
	HIZ = 7

class HwSimCommand(IntEnum):
	RESET = ord('r')
	SEND_REPORT = ord('s')
	SET_META = ord('i')
	SET_FLAGS = ord('f')
	CFG_VECTOR = ord('v')
	EXECUTE = ord('e')
	HIZ = ord('z')

class CompType(IntEnum):
	CONCURRENT = 0
	SEQUENTIAL = 1

#
# CLASSES
# =======
class Communication:
	def __init__(self, port_name, impl):
		self.impl = impl

		try:
			self.comm = serial.Serial(port=port_name, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=300.0)
		except:
			log.error("Couldn't find serial port: " + comm)

		if not self.comm.isOpen():
			log.error("Couldn't open serial port: " + comm)

	def __checkSum(self, blist, len):
		chksum = 0
		for e in range(len):
			chksum += (int(blist[e]))
		return chksum & 0xFF

	def __getTestcaseVectorCount(self, tc):
		count = 0
		for v in self.impl.vs:
			if v.testcase == tc:
				count += 1
		return count

	def __printFailedSignals(self, val):
		l = []
		for i in range(32):
			if (val & 1 << i):
				l.append(i)
		if not len(l) == 0:
			log.note("Expectations not met: " + str(l))
		else:
			log.note("Expectations OK")

	def __fetchReport(self):
		log.info("REPORT:")

		failed_vectors = 0
		vectors_per_tc = self.__getTestcaseVectorCount(self.cur_testcase)
		byte_cnt = 3 + 4 * vectors_per_tc
		report = self.comm.read(byte_cnt)
		chksum = self.__checkSum(report, byte_cnt - 1)
		if not report[byte_cnt - 1] == chksum:
			log.info("Checksum mismatch: {0:d} != {1:d}".format(report[byte_cnt - 1], chksum))
			return False
		for v in range(vectors_per_tc):
			val = 0
			i = 0
			log.info("Vector {0:d}/{1:d}:".format(v + 1, vectors_per_tc))
			vec_rep_start = 2 + (v * 4)
			for b in report[vec_rep_start:vec_rep_start+4]:
				m = i % 4
				if m == 0:
					val += b
				elif m == 1:
					val += b << 8
				elif m == 2:
					val += b << 16
				elif m == 3:
					val += b << 24
				i += 1
			if val:
				failed_vectors += 1
			self.__printFailedSignals(val)
		if failed_vectors:
			self.impl.failed_testcases += 1
		return True

	def __sendCmd(self, command):
		comm_map = {
			CommandType.RESET: HwSimCommand.RESET,
			CommandType.SET_META: HwSimCommand.SET_META,
			CommandType.SET_FLAGS: HwSimCommand.SET_FLAGS,
			CommandType.CFG_VECTOR: HwSimCommand.CFG_VECTOR,
			CommandType.DEF_VECTOR: HwSimCommand.CFG_VECTOR,
			CommandType.SEND_REPORT: HwSimCommand.SEND_REPORT,
			CommandType.EXECUTE: HwSimCommand.EXECUTE,
			CommandType.HIZ: HwSimCommand.HIZ
		}

		switcher = {
			CommandType.RESET: self.__sendCmdReset,
			CommandType.SET_META: self.__sendCmdMeta,
			CommandType.SET_FLAGS: self.__sendCmdFlags,
			CommandType.CFG_VECTOR: self.__sendVector,
			CommandType.DEF_VECTOR: self.__sendDefaultVector,
			CommandType.SEND_REPORT: self.__sendReport,
			CommandType.EXECUTE: self.__sendExecute,
			CommandType.HIZ: self.__sendHiz
		}

		func = switcher.get(command)
		func()
		resp = self.comm.read(1)
		command_str = str(command).split('.')[1]
		if resp == b'O':
			log.info("Request '{0:s}' OK".format(command_str))
		else:
			log.info("Request '{0:s}' failed, response={1:s}".format(command_str, str(resp)))
			return False;

		if command == CommandType.SEND_REPORT:
			return self.__fetchReport()
		return True

	def __sendCmdReset(self):
		log.info("Resetting simulator")
		self.comm.write(b'rr')

	def __sendCmdMeta(self):
		log.info("Sending meta")

		bytelist = []
		bytelist.append(int(HwSimCommand.SET_META))
		if self.impl.md.comp_type == 'c':
			bytelist.append(int(CompType.CONCURRENT))
			bytelist.append(0xFF)
		else:
			bytelist.append(int(CompType.SEQUENTIAL))
			bytelist.append(self.impl.md.clock_def)
		bytelist.append(self.impl.md.testcases)
		bytelist.append(self.impl.md.vectors)
		bytelist.append(self.impl.md.signals)
		for e in self.impl.md.clock_period.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for e in self.impl.md.interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("Meta frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendCmdFlags(self):
		log.info("Sending flags")

		bytelist = []
		bytelist.append(int(HwSimCommand.SET_FLAGS))
		bytelist.append(self.cur_testcase)
		bytelist.append(self.impl.flags[self.cur_testcase])
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("Flags frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendDefaultVector(self):
		log.info("Sending default vector")

		bytelist = []
		bytelist.append(int(HwSimCommand.CFG_VECTOR))
		bytelist.append(self.impl.dv.vector_num)
		bytelist.append(self.impl.dv.testcase)
		for e in self.impl.dv.interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for s in self.impl.sm:
			bytelist.append(ord(self.impl.dv.content[s]))
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("Default vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendVector(self):
		log.info("Sending vector")

		bytelist = []
		bytelist.append(int(HwSimCommand.CFG_VECTOR))
		bytelist.append(self.impl.vs[self.cur_vec].vector_num)
		bytelist.append(self.impl.vs[self.cur_vec].testcase)
		for e in self.impl.vs[self.cur_vec].interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for s in self.impl.sm:
			bytelist.append(ord(self.impl.vs[self.cur_vec].content[s]))
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("Vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendReport(self):
		log.info("Requesting current report")

		self.comm.write(b'ss')

	def __sendExecute(self):
		log.info("Requesting execute vector {0:d}/{1:d}".format(self.cur_vec_execute, len(self.impl.vs)))

		self.comm.write(b'ee')

	def __sendHiz(self):
		log.info("Sending hiz {0:d}->{1:d}".format(self.impl.hiz[self.cur_hiz][0], self.impl.hiz[self.cur_hiz][1]))

		bytelist = []
		bytelist.append(int(HwSimCommand.HIZ))
		bytelist.append(self.impl.hiz[self.cur_hiz][0])
		bytelist.append(self.impl.hiz[self.cur_hiz][1])
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("HIZ frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def sendReset(self):
		if not self.__sendCmd(CommandType.RESET):
			return False
		return True

	def initSim(self):
		if not self.__sendCmd(CommandType.RESET):
			return False
		if not self.__sendCmd(CommandType.SET_META):
			return False
		if not self.__sendCmd(CommandType.DEF_VECTOR):
			return False
		return True

	def sendHiz(self):
		self.cur_hiz = 0
		for n in range(len(self.impl.hiz)):
			if not self.__sendCmd(CommandType.HIZ):
				return False
			self.cur_hiz += 1
		return True

	def sendVectors(self):
		self.cur_vec = 0
		for n in range(self.impl.md.vectors):
			if not self.__sendCmd(CommandType.CFG_VECTOR):
				return False
			self.cur_vec += 1
		return True

	def sendFlags(self):
		self.cur_testcase = 0
		for n in range(self.impl.md.testcases):
			if not self.__sendCmd(CommandType.SET_FLAGS):
				return False
			self.cur_testcase += 1
		return True

	def executeTests(self):
		self.cur_vec_execute = 1
		for tc in range(self.impl.md.testcases):
			log.info("Executing test {0:d}/{1:d}".format(tc + 1, self.impl.md.testcases))
			for vec in self.impl.vs:
				if vec.testcase == tc:
					if not self.__sendCmd(CommandType.EXECUTE):
						return False
					self.cur_vec_execute += 1
			self.cur_testcase = tc
			if not self.__sendCmd(CommandType.SEND_REPORT):
				return False
		return True

class Metadata:
	comp_type = None
	signals = None
	testcases = None
	vectors = None
	interval = None
	clock_period = None

	def __init__(self, fpath):
		md_file = open(fpath)
		md = md_file.readline().split(';')
		md_file.close()
		self.comp_type = md[0].split(':')[1]
		self.signals = int(md[1].split(':')[1])
		self.testcases = int(md[2].split(':')[1])
		self.vectors = int(md[3].split(':')[1])
		self.interval = int(intervalToNs(md[4]))
		self.clock_period = int(clockToNs(md[5]))

		if self.comp_type == 's':
			clk_def = md[0].split(':')[2]
			if clk_def == 'l':
				self.clock_def = 0
			else:
				self.clock_def = 1
		else:
			self.clock_def = 'x'

	def __str__(self):
		return "comp_type: {0:s}; signals: {1:d}; testcases: {2:d}; vectors: {3:d}; interval: {4:d}ns; clk: {5:0.2f}ns ({6:s})"\
			.format(self.comp_type, self.signals, self.testcases, self.vectors, self.interval, self.clock_period / 100.0, str(self.clock_def))

class Vector:
	vector_num = None
	testcase = None
	content = None
	interval = None

	def __str__(self):
		return "vector_num: {0:d}; testcase: {1:d}; content: {2:s}; interval: {3:d}ns"\
			.format(self.vector_num + 1, self.testcase + 1, self.content, self.interval)

#
# IMPLEMENTATION
# ==============
class Impl:
	def __init__(self, target_sim_path, comm, comp, verbose):
		log.setVerbose(verbose)
		self.failed_testcases = 0
		self.communication = Communication(comm, self)

		self.comp = comp
		self.target_sim_path = target_sim_path

		self.metadata_file_path = target_sim_path + "/" + comp + ".mi"
		self.map_file_path = target_sim_path + "/" + comp + ".map"
		self.def_vector_path = target_sim_path + "/" + comp + "_df.vec"

		if not os.path.exists(self.metadata_file_path):
			log.error("Couldn't find metadata file: " + self.metadata_file_path)

		if not os.path.exists(self.def_vector_path):
			log.error("Couldn't find default vector file: " + self.def_vector_path)

		if not os.path.exists(self.map_file_path):
			log.error("Couldn't find map file: " + self.map_file_path)

	def __loadDefaultVector(self, fpath):
		dv_file = open(fpath)
		for line in dv_file:
			if line.startswith("#"):
				continue
		dv_file.close()

		line = line.replace('#', '').replace(' ', '')
		def_vec = Vector()
		def_vec.testcase = 0xFF
		def_vec.vector_num = 0xFF
		def_vec.content = line
		def_vec.interval = 0xFFFFFFFF

		return def_vec

	def __loadSignalMap(self, fpath):
		map_file = open(fpath)
		line = map_file.readline()
		map_file.close()

		signals = line.split(' ')
		count = len(signals)
		sig_map = []
		hiz_map = []
		for s in range(count):
			e = signals[s].split(':')
			sig_map.append(int(e[1]))
			if len(e) == 3:
				hiz_map.append((int(e[0]), int(e[2])))

		return sig_map, hiz_map

	def __loadVectors(self, files):
		vs = []
		flags = []
		vector_no = 0

		for f in files:
			tc = int(f[len(f)-6:len(f)-4])
			vf = open(f)
			for l in vf:
				if l.startswith("#flags"):
					flag_r = int(l.split(" ")[1].split(":")[1][0])
					flag_cd = int(l.split(" ")[2].split(":")[1][0])
					flag_cr = int(l.split(" ")[3].split(":")[1][0])
					continue
				if l.startswith("#"):
					continue
				l = l.lstrip().replace("\n", "")
				interval = intervalStrToNs(l[0:4])
				v = Vector()
				v.vector_num = vector_no
				v.testcase = tc - 1
				v.content = l[5:].replace(" ", "")
				v.interval = interval
				vs.append(v)

				vector_no += 1
			flags.append((flag_r << 0) | (flag_cd << 1) | (flag_cr << 2))
			vf.close()
		return vs, flags

	def run(self):
		log.info("Loading metadata")
		self.md = Metadata(self.metadata_file_path)
		log.info("Metadata = " + str(self.md))

		log.info("Loading signal map")
		self.sm, self.hiz = self.__loadSignalMap(self.map_file_path)
		log.info("SignalMap = " + str(self.sm))

		log.info("Loading default vector")
		self.dv = self.__loadDefaultVector(self.def_vector_path)
		log.info("DefVector = " + str(self.dv))

		log.info("Building vector file list")
		vec_list = glob.glob(self.target_sim_path + "/" + self.comp + "*.vec")
		for vec in vec_list:
			if not vec.find("df.vec") == -1:
				vec_list.remove(vec)
		vec_list.sort()
		log.info("VectorFiles = " + str(vec_list))

		log.info("Building vectors list")
		self.vs, self.flags = self.__loadVectors(vec_list)
		log.info("Vectors:")
		for v in self.vs:
			log.info(str(v))
		if not len(self.vs) == self.md.vectors:
			log.error("Vectors count mismatch: {0:d} != {1:d}".format(len(self.vs), self.md.vectors))

		if not self.communication.initSim():
			log.error("HW simulator initialization failed")
		log.info("HW simulator initialization OK")

		if not self.communication.sendHiz():
			log.error("Couldn't send HIZ information")
		log.info("HW simulator sending HIZ OK")

		if not self.communication.sendVectors():
			log.error("Couldn't send vectors")
		log.info("HW simulator sending vectors OK")

		if not self.communication.sendFlags():
			log.error("Couldn't send flags")
		log.info("HW simulator sending flags OK")

		self.communication.executeTests()
		log.info("FINISHED (failed {0:d} of {1:d} testcases)".format(self.failed_testcases, self.md.testcases))

		if not self.communication.sendReset():
			log.error("HW simulator RESET failed")
		else:
			log.info("HW simulator RESET OK")

		return
#
# RUN
# ===
def run():
	global verbose
	arg_parser = argparse.ArgumentParser(description=app_description, epilog=app_epilog,\
		prog=app_prog, formatter_class=argparse.RawDescriptionHelpFormatter)

	arg_parser.add_argument("comp", help="component name")

	arg_parser.add_argument("--com", help="UART communication port", required=True)

	arg_parser.add_argument("--verbose", help="more verbose logging", action="store_true")
	arg_parser.add_argument("--version", action="version", version="%(prog)s-" + app_version)

	args = arg_parser.parse_args()

	comm = args.com
	comp = args.comp
	verbose = args.verbose

	app_dir = os.path.dirname(exec_name)
	target_sim_path = os.path.realpath(app_dir + "/../../target_sim")
	if not os.path.isdir(target_sim_path):
		log.error("Directory {0:s} doesn't exist".format(target_sim_path))

	app = Impl(target_sim_path, comm, comp, verbose)
	app.run()

# ENTRY POINT
# ===========
if __name__ == "__main__":
	run()
