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

	def __init__(self, md_file):
		md_file = open(md_file)
		md = md_file.readline().split(';')
		self.signals = int(md[0].split(':')[1])
		self.testcases = int(md[1].split(':')[1])
		self.interval = md[2]
		md_file.close()

	def __str__(self):
		return "signals: {0:d}; testcases: {1:d}; interval: {2:d}ns"\
			.format(self.signals, self.testcases, intervalToNs(self.interval))

#
# IMPLEMENTATION
# ==============
class Impl:
	def __init__(self, target_sim_path, comm, comp, verbose):
		self.comp = comp
		self.target_sim_path = target_sim_path
		log.setVerbose(verbose)

		self.metadata_file_path = target_sim_path + "/" + comp + ".mi"
		self.map_file_path = target_sim_path + "/" + comp + ".map"

		if not os.path.exists(self.metadata_file_path):
			log.error("Couldn't find metadata file: " + self.metadata_file_path)

		if not os.path.exists(self.map_file_path):
			log.error("Couldn't find map file: " + self.map_file_path)

		try:
			self.comm = serial.Serial(port=comm, baudrate=115200, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
		except:
			log.error("Couldn't find serial port: " + comm)

		if not self.comm.isOpen():
			log.error("Couldn't open serial port: " + comm)

	def run(self):
		log.info("Loading metadata")
		self.md = Metadata(self.metadata_file_path)
		log.info("Metadata = " + str(self.md))

		log.info("Building vector list")
		vec_list = glob.glob(self.target_sim_path + "/" + self.comp + "*.vec")
		for vec in vec_list:
			if not vec.find("df.vec") == -1:
				vec_list.remove(vec)
		vec_list.sort()
		self.vec_list = vec_list

		log.info("Vectors: " + str(self.vec_list))

		log.info("Resetting simulator")
		self.comm.write(b'RR')
		print(self.comm.read(10))
		log.info("Mapping singals")

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
