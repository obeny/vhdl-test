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
		"ms": 1000,
		"s": 1000 * 1000
	}
	return switcher.get(mul) * value

#
# ENUMS
# =====
class CommandType(IntEnum):
	RESET = 0
	SET_TC_NAME = 1
	SEND_REPORT = 2
	SET_META = 3
	CFG_VECTOR = 4
	DEF_VECTOR = 5
	EXECUTE = 6

class HwSimCommand(IntEnum):
	RESET = ord('r')
	SET_TC_NAME = ord('n')
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
			self.comm = serial.Serial(port=port_name, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
		except:
			log.error("Couldn't find serial port: " + comm)

		if not self.comm.isOpen():
			log.error("Couldn't open serial port: " + comm)

	def __checkSum(self, blist):
		chksum = 0
		for e in blist:
			chksum += (int(e))
		return chksum & 0xFF

	def __sendCmd(self, command):
		comm_map = {
			CommandType.RESET: HwSimCommand.RESET,
			CommandType.SET_META: HwSimCommand.SET_META,
			CommandType.CFG_VECTOR: HwSimCommand.CFG_VECTOR,
			CommandType.DEF_VECTOR: HwSimCommand.CFG_VECTOR,
		}

		switcher = {
			CommandType.RESET: self.__sendCmdReset,
			CommandType.SET_META: self.__sendCmdMeta,
			CommandType.CFG_VECTOR: self.__sendVector,
			CommandType.DEF_VECTOR: self.__sendDefaultVector
		}

		func = switcher.get(command)
		func()
		resp = self.comm.read(100)
		command_str = str(command).split('.')[1]
		if resp == b'O':
			log.info("Request '{0:s}' OK".format(command_str))
			return True
		log.info("Request '{0:s}' failed, response={1:s}".format(command_str, str(resp)))
		return False

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
		bytelist.append(self.__checkSum(bytelist))

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
		bytelist.append(self.__checkSum(bytelist))

		log.info("Default vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendVector(self):
		log.info("Sending vector")

	def initSim(self):
		if not self.__sendCmd(CommandType.RESET):
			return False
		if not self.__sendCmd(CommandType.SET_META):
			return False
		if not self.__sendCmd(CommandType.DEF_VECTOR):
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
		log.info("NOT IMPLEMENTED")

		if self.communication.initSim():
			log.info("HW simulator initialization OK")
		else:
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
