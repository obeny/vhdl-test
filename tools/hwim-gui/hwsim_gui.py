#!/usr/bin/env python3

import argparse
import glob
import os
import serial
import sys

import log

from enum import IntEnum

verbose=False
exec_name=os.path.realpath(sys.argv[0])

app_version = "0.7"
app_prog = os.path.splitext(os.path.basename(exec_name))[0]

app_description = "Executes generated test vectors on hardware simulator."
app_epilog = app_prog + " version: " + app_version + "\nCopyright (C) 2019 - Marcin 'obeny' Benka <marcin.benka@gmail.com>\n\
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

	return (((1000 * 1000 * 1000) / switcher.get(div)) * 1000) / value

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
	DEVICE_INFO = 8

class HwSimCommand(IntEnum):
	RESET = ord('r')
	SEND_REPORT = ord('s')
	SET_META = ord('i')
	SET_FLAGS = ord('f')
	CFG_VECTOR = ord('v')
	EXECUTE = ord('e')
	HIZ = ord('z')
	DEVICE_INFO = ord('d')

class CompType(IntEnum):
	CONCURRENT = 0
	SEQUENTIAL = 1

#
# CLASSES
# =======
class DeviceInfo:
	platform = ""
	platform_ver = 0
	gpio_cnt = 0
	testcase_cnt_max = 0
	vectors_cnt_max = 0

	def __str__(self):
		major = int(self.platform_ver >> 4)
		minor = int(self.platform_ver & 0xF)
		ver = "{0:d}.{1:d}".format(major, minor)

		return ("platform: {0:s}-{1:s}, gpios: {2:d}, testcases: {3:d}, vectors: {4:d}"\
			.format(self.platform, ver, self.gpio_cnt, self.testcase_cnt_max, self.vectors_cnt_max))

class Communication:
	def __init__(self, port_name, impl):
		self.impl = impl

		try:
			self.comm = serial.Serial(port=port_name, baudrate=230400, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=300.0)
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
			sigs = ""
			for le in l:
				sigs += "[{0:d}]->{1:s} ".format(le, self.impl.sm[le][1])
			log.warning("Expectations not met: " + log.TermColor.RED + sigs + log.TermColor.NC)
		else:
			log.info("Expectations " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

	def __fetchReport(self):
		failed_vectors = 0
		vectors_per_tc = self.__getTestcaseVectorCount(self.cur_testcase)
		byte_cnt = 3 + 4 * vectors_per_tc + 2 + 4
		report = self.comm.read(byte_cnt)
		chksum = self.__checkSum(report, byte_cnt - 1)
		if not report[byte_cnt - 1] == chksum:
			log.warning("Checksum mismatch: {0:d} != {1:d}".format(report[byte_cnt - 1], chksum))
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

		clk_ticks = report[vec_rep_start + 4]
		clk_ticks += report[vec_rep_start + 5] << 8

		ns = report[vec_rep_start + 4 + 2]
		ns += report[vec_rep_start + 4 + 3] << 8
		ns += report[vec_rep_start + 4 + 4] << 16
		ns += report[vec_rep_start + 4 + 5] << 24

		if self.impl.md.comp_type == 's':
			log.info("Total clock ticks: {0:d}; Total time: {1:d} ns".format(clk_ticks, ns))
		return True

	def __fetchDeviceInfo(self):
		di = DeviceInfo()
		byte_cnt = 7 + 32 + 1
		device_info = self.comm.read(byte_cnt)
		chksum = self.__checkSum(device_info, byte_cnt - 1)
		if not device_info[byte_cnt - 1] == chksum:
			log.warning("Checksum mismatch: {0:d} != {1:d}".format(device_info[byte_cnt - 1], chksum))
			return False
		di.gpio_cnt = device_info[1]
		di.testcase_cnt_max = int(device_info[2])
		di.vectors_cnt_max = int(device_info[3]) + int(device_info[4] << 4)
		di.platform_ver = int(device_info[5])
		platform_name_len = int(device_info[6])
		di.platform = str(device_info[7:platform_name_len+7].decode())
		log.info("Hwsim: " + str(di))
		self.impl.device_info = di
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
			CommandType.HIZ: HwSimCommand.HIZ,
			CommandType.DEVICE_INFO: HwSimCommand.DEVICE_INFO,
		}

		switcher = {
			CommandType.RESET: self.__sendCmdReset,
			CommandType.SET_META: self.__sendCmdMeta,
			CommandType.SET_FLAGS: self.__sendCmdFlags,
			CommandType.CFG_VECTOR: self.__sendVector,
			CommandType.DEF_VECTOR: self.__sendDefaultVector,
			CommandType.SEND_REPORT: self.__sendReport,
			CommandType.EXECUTE: self.__sendExecute,
			CommandType.HIZ: self.__sendHiz,
			CommandType.DEVICE_INFO: self.__sendDeviceInfo,
		}

		func = switcher.get(command)
		func()
		resp = self.comm.read(1)
		command_str = str(command).split('.')[1]
		if resp == b'O':
			log.debug("Request '{0:s}' OK".format(command_str))
		else:
			log.info("Request '{0:s}' failed, response={1:s}".format(command_str, str(resp)))
			return False;

		if command == CommandType.SEND_REPORT:
			return self.__fetchReport()
		elif command == CommandType.DEVICE_INFO:
			return self.__fetchDeviceInfo()
		return True

	def __sendCmdReset(self):
		log.note("Resetting simulator")
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
		bytelist.append(self.impl.md.vectors & 0xFF)
		bytelist.append((self.impl.md.vectors >> 8) & 0xFF)
		bytelist.append(self.impl.md.signals)
		for e in self.impl.md.clock_period.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for e in self.impl.md.interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.debug("Meta frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendCmdFlags(self):
		log.info("Sending flags")

		bytelist = []
		bytelist.append(int(HwSimCommand.SET_FLAGS))
		bytelist.append(self.cur_testcase)
		bytelist.append(self.impl.flags[self.cur_testcase])
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.debug("Flags frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendDefaultVector(self):
		log.info("Sending default vector")

		bytelist = []
		bytelist.append(int(HwSimCommand.CFG_VECTOR))
		bytelist.append(self.impl.dv.vector_num & 0xFF)
		bytelist.append((self.impl.dv.vector_num >> 8) & 0xFF)
		bytelist.append(self.impl.dv.testcase)
		for e in self.impl.dv.interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for s in self.impl.sm:
			bytelist.append(ord(self.impl.dv.content[int(s[2])]))
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.debug("Default vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendVector(self):
		log.note("Sending vector {0:d}/{1:d}".format(self.cur_vec + 1, self.impl.md.vectors))

		bytelist = []
		bytelist.append(int(HwSimCommand.CFG_VECTOR))
		bytelist.append(self.impl.vs[self.cur_vec].vector_num & 0xFF)
		bytelist.append((self.impl.vs[self.cur_vec].vector_num >> 8) & 0xFF)
		bytelist.append(self.impl.vs[self.cur_vec].testcase)
		for e in self.impl.vs[self.cur_vec].interval.to_bytes(4, byteorder="little"):
			bytelist.append(e)
		for s in self.impl.sm:
			bytelist.append(ord(self.impl.vs[self.cur_vec].content[s[2]]))
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.debug("Vector frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendReport(self):
		log.note("Requesting current report")

		self.comm.write(b'ss')

	def __sendExecute(self):
		log.note("Requesting execute vector {0:d}/{1:d}".format(self.cur_vec_execute, len(self.impl.vs)))

		self.comm.write(b'ee')

	def __sendHiz(self):
		log.note("Sending hiz {0:d}->{1:d}".format(self.impl.hiz[self.cur_hiz][0], self.impl.hiz[self.cur_hiz][1]))

		bytelist = []
		bytelist.append(int(HwSimCommand.HIZ))
		bytelist.append(self.impl.hiz[self.cur_hiz][0])
		bytelist.append(self.impl.hiz[self.cur_hiz][1])
		bytelist.append(self.__checkSum(bytelist, len(bytelist)))

		log.debug("HIZ frame = " + str(bytelist))
		self.comm.write(bytearray(bytelist))

	def __sendDeviceInfo(self):
		log.note("Requesting device information")

		self.comm.write(b'dd')

	def sendReset(self):
		if not self.__sendCmd(CommandType.RESET):
			return False
		return True

	def discoverHwsim(self):
		if not self.__sendCmd(CommandType.DEVICE_INFO):
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
		self.interval = int(intervalToNs(md[2]))
		self.clock_period = int(clockToNs(md[3]))

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
			.format(self.comp_type, self.signals, self.testcases, self.vectors, self.interval, self.clock_period / 1000.0, str(self.clock_def))

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
	def __init__(self, target_sim_path, comm, comp, tc, verbose):
		log.setVerbose(verbose)
		self.tc = tc
		self.failed_testcases = 0
		self.device_info = None
		self.communication = Communication(comm, self)

		self.comp = comp
		self.target_sim_path = target_sim_path

		self.metadata_file_path = target_sim_path + "/" + comp + ".mi"
		self.map_file_path = target_sim_path + "/" + comp + ".map"
		self.def_vector_path = target_sim_path + "/" + comp + "_df.vec"

		if not os.path.exists(self.metadata_file_path):
			log.fatal("Couldn't find metadata file: " + self.metadata_file_path)

		if not os.path.exists(self.def_vector_path):
			log.fatal("Couldn't find default vector file: " + self.def_vector_path)

		if not os.path.exists(self.map_file_path):
			log.fatal("Couldn't find map file: " + self.map_file_path)

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
		sig_map = []
		hiz_map = []
		for s in range(len(signals)):
			e = signals[s].split(':')
			n = e[0].split("-")
			sig_map.append((int(n[0]), n[1], int(e[1])))
			if n[1][0] == 'Z':
				if len(e) == 3:
					hiz_map.append((int(e[0].split("-")[0]), int(e[2])))
				else:
					log.fatal("HI-Z signal \"{0:s}\" do not have validation pin defined".format(n[1]))

		return sig_map, hiz_map

	def __loadVectors(self, files):
		vs = []
		flags = []
		vector_no = 0

		tc = 0
		for f in files:
			tc += 1
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
		log.note("Loading signal map")
		self.sm, self.hiz = self.__loadSignalMap(self.map_file_path)
		log.debug("SignalMap = " + str(self.sm))

		log.note("Loading metadata")
		self.md = Metadata(self.metadata_file_path)

		log.note("Loading default vector")
		self.dv = self.__loadDefaultVector(self.def_vector_path)
		log.debug("DefVector = " + str(self.dv))

		log.note("Building vector file list")
		if self.tc:
			vec_list = []
			for i in self.tc:
				vec_list.append(self.target_sim_path + "/" + self.comp + "_{0:02d}.vec".format(int(i)))
		else:
			vec_list = glob.glob(self.target_sim_path + "/" + self.comp + "*.vec")
		for vec in vec_list:
			if not vec.find("df.vec") == -1:
				vec_list.remove(vec)
		vec_list.sort()
		self.md.testcases = len(vec_list)
		log.debug("VectorFiles = " + str(vec_list))

		log.note("Building vectors list")
		self.vs, self.flags = self.__loadVectors(vec_list)
		log.debug("Vectors:")
		for v in self.vs:
			log.debug(str(v))
		self.md.vectors = len(self.vs)

		log.note("Metadata = " + str(self.md))

		if not self.communication.discoverHwsim():
			log.error("HW simulator discovery failed")
		log.info("HW simulator discovery " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		if len(self.vs) > self.device_info.vectors_cnt_max:
			log.error("Vector count not supported by hwsim ({0:d}/{1:d})".format(len(self.vs), self.device_info.vectors_cnt_max))

		if not self.communication.initSim():
			log.error("HW simulator initialization failed")
		log.info("HW simulator initialization " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		if not self.communication.sendHiz():
			log.error("Couldn't send HIZ information")
		log.info("HW simulator sending HIZ " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		if not self.communication.sendVectors():
			log.error("Couldn't send vectors")
		log.info("HW simulator sending vectors " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		if not self.communication.sendFlags():
			log.error("Couldn't send flags")
		log.info("HW simulator sending flags " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		self.communication.executeTests()
		if self.failed_testcases > 0:
			log.warning((log.TermColor.RED + "FINISHED (failed {0:d} of {1:d} testcases)" + log.TermColor.NC).format(self.failed_testcases, self.md.testcases))
		else:
			log.info((log.TermColor.LGREEN + "FINISHED (failed {0:d} of {1:d} testcases)" + log.TermColor.NC).format(self.failed_testcases, self.md.testcases))

		if not self.communication.sendReset():
			log.error("HW simulator RESET failed")
		else:
			log.note("HW simulator RESET " + log.TermColor.LGREEN + "OK" + log.TermColor.NC)

		return
#
# RUN
# ===
def run():
	arg_parser = argparse.ArgumentParser(description=app_description, epilog=app_epilog,\
		prog=app_prog, formatter_class=argparse.RawDescriptionHelpFormatter)

	arg_parser.add_argument("comp", help="component name <required>")

	arg_parser.add_argument("--com", help="UART communication port <required>", required=True)
	arg_parser.add_argument("--tc", help="run only given testcases; comma delimeted, e.g. 1,2-5,7")

	arg_parser.add_argument("--verbose", help="logging verbosity (note, debug)", nargs='?', choices=['note', 'debug'])
	arg_parser.add_argument("--version", action="version", version="%(prog)s-" + app_version)

	args = arg_parser.parse_args()

	comm = args.com
	comp = args.comp

	tc_list = None
	if args.tc:
		tc_list = []
		for tc in args.tc.split(','):
			if '-' in tc:
				r = tc.split('-')
				b = int(r[0])
				e = int(r[1])
				for i in range(b, e + 1):
					tc_list.append(i)
			else:
				tc_list.append(int(tc))
		tc_set = set(tc_list)
		tc_list = list (tc_set)
		tc_list.sort()

	if args.verbose == 'note':
		verbose = log.Verbosity.NOTE
	elif args.verbose == 'debug':
		verbose = log.Verbosity.DEBUG
	else:
		verbose = log.Verbosity.INFO

	app_dir = os.path.dirname(exec_name)
	target_sim_path = os.path.realpath(app_dir + "/../../target_sim")
	if not os.path.isdir(target_sim_path):
		log.fatal("Directory {0:s} doesn't exist".format(target_sim_path))

	app = Impl(target_sim_path, comm, comp, tc_list, verbose)
	log.info("running hwsim")
	app.run()

# ENTRY POINT
# ===========
if __name__ == "__main__":
	run()
