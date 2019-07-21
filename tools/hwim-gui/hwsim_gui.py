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
	CFG_VECTOR = 3
	DEF_VECTOR = 4
	EXECUTE = 5

class HwSimCommand(IntEnum):
	RESET = ord('r')
	SEND_REPORT = ord('s')
	SET_META = ord('i')
	CFG_VECTOR = ord('v')
	EXECUTE = ord('e')

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
			self.comm = serial.Serial(port=port_name, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0.2)
		except:
			log.error("Couldn't find serial port: " + comm)

		if not self.comm.isOpen():
			log.error("Couldn't open serial port: " + comm)

	def __checkSum(self, blist, len):
		chksum = 0
		for e in range(len):
			chksum += (int(blist[e]))
		return chksum & 0xFF

	def __fetchReport(self):
		log.info("REPORT:")

		byte_cnt = 4 + self.impl.md.testcases
		report = self.comm.read(byte_cnt)
		chksum = self.__checkSum(report, byte_cnt - 1)
		if not report[byte_cnt - 1] == chksum:
			log.info("Checksum mismatch: {0:d} != {1:d}".format(report[byte_cnt - 1], chksum))
			return False
		log.info("failed={0:d}; broken_frames={1:d}".format(report[1], report[2]))
		for tc in range(self.impl.md.testcases):
			log.info("TC={0:d}; failures={1:d}".format(tc, report[tc+3]))
		return True

	def __sendCmd(self, command):
		comm_map = {
			CommandType.RESET: HwSimCommand.RESET,
			CommandType.SET_META: HwSimCommand.SET_META,
			CommandType.CFG_VECTOR: HwSimCommand.CFG_VECTOR,
			CommandType.DEF_VECTOR: HwSimCommand.CFG_VECTOR,
			CommandType.SEND_REPORT: HwSimCommand.SEND_REPORT,
			CommandType.EXECUTE: HwSimCommand.EXECUTE
		}

		switcher = {
			CommandType.RESET: self.__sendCmdReset,
			CommandType.SET_META: self.__sendCmdMeta,
			CommandType.CFG_VECTOR: self.__sendVector,
			CommandType.DEF_VECTOR: self.__sendDefaultVector,
			CommandType.SEND_REPORT: self.__sendReport,
			CommandType.EXECUTE: self.__sendExecute
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
		else:
			bytelist.append(int(CompType.SEQUENTIAL))
		bytelist.append(self.impl.md.testcases)
		bytelist.append(self.impl.md.vectors)
		bytelist.append(self.impl.md.signals)
		for e in self.impl.md.clock_period.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for e in self.impl.md.interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		bytelist.append(self.__checkSum(bytelist, len(bytelist)-1))

		log.info("Meta frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendDefaultVector(self):
		log.info("Sending default vector")

		bytelist = []
		bytelist.append(int(HwSimCommand.CFG_VECTOR))
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
		bytelist.append(self.impl.vs[self.cur_vec].testcase)
		for e in self.impl.vs[self.cur_vec].interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for s in self.impl.sm:
			bytelist.append(ord(self.impl.dv.content[s]))
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.info("Vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendReport(self):
		log.info("Requesting current report")

		self.comm.write(b'ss')

	def __sendExecute(self):
		log.info("Requesting execute vector")

		self.comm.write(b'ee')

	def initSim(self):
		if not self.__sendCmd(CommandType.RESET):
			return False
		if not self.__sendCmd(CommandType.SET_META):
			return False
		if not self.__sendCmd(CommandType.DEF_VECTOR):
			return False
		return True

	def sendVectors(self):
		self.cur_vec = 0
		for n in range(self.impl.md.vectors):
			if not self.__sendCmd(CommandType.CFG_VECTOR):
				return False
			self.cur_vec += 1
		return True

	def executeTests(self):
		for tc in range(self.impl.md.testcases):
			log.info("Executing test {0:d}/{1:d}".format(tc + 1, self.impl.md.testcases))
			if not self.__sendCmd(CommandType.EXECUTE):
				return False
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
		self.clock_period = 0

	def __str__(self):
		return "comp_type: {0:s}; signals: {1:d}; testcases: {2:d}; vectors: {3:d}; interval: {4:d}ns; clk_period: {5:d}ns"\
			.format(self.comp_type, self.signals, self.testcases, self.vectors, self.interval, self.clock_period)

class Vector:
	testcase = None
	content = None
	interval = None

	def __str__(self):
		return "testcase: {0:d}; content: {1:s}; interval: {2:d}ns"\
			.format(self.testcase, self.content, self.interval)

#
# IMPLEMENTATION
# ==============
class Impl:
	def __init__(self, target_sim_path, comm, comp, verbose):
		log.setVerbose(verbose)
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
		for s in range(count):
			sig_map.append(int(signals[s].split(':')[1])) 

		return sig_map

	def __loadVectors(self, files):
		vs = []

		for f in files:
			tc = int(f[len(f)-6:len(f)-4])
			vf = open(f)
			for l in vf:
				if l.startswith("#"):
					continue
				l = l.lstrip().replace("\n", "")
				interval = intervalStrToNs(l[0:4])
				v = Vector()
				v.testcase = tc
				v.content = l[5:].replace(" ", "")
				v.interval = interval
				vs.append(v)
			vf.close()
		return vs

	def run(self):
		log.info("Loading metadata")
		self.md = Metadata(self.metadata_file_path)
		log.info("Metadata = " + str(self.md))

		log.info("Loading signal map")
		self.sm = self.__loadSignalMap(self.map_file_path)
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
		self.vs = self.__loadVectors(vec_list)
		log.info("Vectors:")
		for v in self.vs:
			log.info(str(v))
		if not len(self.vs) == self.md.vectors:
			log.error("Vectors count mismatch: {0:d} != {1:d}".format(len(self.vs), self.md.vectors))

		if not self.communication.initSim():
			log.error("HW simulator initialization failed")
		log.info("HW simulator initialization OK")

		if not self.communication.sendVectors():
			log.error("Couldn't send vectors")
		log.info("HW simulator sending vectors OK")

		self.communication.executeTests()
		log.info("FINISHED")

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
