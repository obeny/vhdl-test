#!/usr/bin/env python3

import glob
import argparse
import os
import serial
import sys

import log

verbose=False
python_req_version = (3, 0, 1)
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
# CLASSES
# =======
class Metadata:
	signals = None
	testcases = None
	interval = None
	comp_type = None

	def __init__(self, fpath):
		md_file = open(fpath)
		md = md_file.readline().split(';')
		md_file.close()
		self.comp_type = md[0].split(':')[1]
		self.signals = int(md[1].split(':')[1])
		self.testcases = int(md[2].split(':')[1])
		self.interval = md[3]

	def __str__(self):
		return "comp_type: {0:s}; signals: {1:d}; testcases: {2:d}; interval: {3:d}ns"\
			.format(self.comp_type, self.signals, self.testcases, intervalToNs(self.interval))

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

		try:
			self.comm = serial.Serial(port=comm, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
		except:
			log.error("Couldn't find serial port: " + comm)

		if not self.comm.isOpen():
			log.error("Couldn't open serial port: " + comm)

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
		def_vec.interval = 0xFFFF

		return def_vec

	def __loadSignalMap(self, fpath):
		map_file = open(fpath)
		line = map_file.readline()
		map_file.close()

		signals = line.split(' ')
		count = len(signals)
		sig_map = []
		for s in range(count):
			sig_map.append(signals[s].split(':')[1])

		return sig_map

	def communicate(self):
		log.info("Resetting simulator")
		self.comm.write(b'RR')
		print(self.comm.read(10))

	def run(self):
		log.info("Loading metadata")
		self.md = Metadata(self.metadata_file_path)
		log.info("Metadata = " + str(self.md))

		log.info("Loading default vector")
		self.dv = self.__loadDefaultVector(self.def_vector_path)
		log.info("DefVector = " + str(self.dv))

		log.info("Loading signal map")
		self.sm = self.__loadSignalMap(self.map_file_path)
		log.info("SignalMap = " + str(self.sm))

		log.info("Building vector file list")
		vec_list = glob.glob(self.target_sim_path + "/" + self.comp + "*.vec")
		for vec in vec_list:
			if not vec.find("df.vec") == -1:
				vec_list.remove(vec)
		vec_list.sort()
		log.info("VectorFiles = " + str(vec_list))

		self.communicate()

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
