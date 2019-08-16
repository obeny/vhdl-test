import glob
import os

import log
import Classes as CLS
import Utils as UT

#
# DEFINITIONS
# ===========

# colors for ISIM gui
color_clock = 'yellow'
color_input = 'green'
color_output = 'red'
color_bidir = 'magenta'
color_tc_num = 'gray'

#
# BACKEND SPECIFIC
# ================
class Generics:
	content = []

class Deps:
	content = []

class Param:
	def __init__(self):
		self.name = ""
		self.type = ""
		self.value = ""

	def __str__(self):
		return "name={0:s}, type={1:s}, value={2:s}"\
			.format(self.name, self.type, self.value)

#
# BACKEND BODY
# ============

# class BackendData - contains backend specific data from XML
class BackendData:
	generics = None
	deps = None

# class BackendDataHandler - builds backend specific data from XML
class BackendDataHandler:

# PUBLIC methods
	def buildData(self, xml_node):
		backend_data = BackendData()
		backend_node = xml_node.find('vhdl')
		if backend_node:
			xml_generics = backend_node.find('generics')
			if xml_generics:
				backend_data.generics = self.__buildGenerics(xml_generics)

			xml_deps = backend_node.find('deps')
			if xml_deps:
				backend_data.deps = self.__buildDeps(xml_deps)
		return backend_data

# PRIVATE methods
	def __buildGenerics(self, xml_generics):
		generics = Generics()
		if xml_generics:
			for xml_node in xml_generics:
				generics.content.append(self.__buildParam(xml_node))

		log.info("buildGenerics: built {0:d} generic(s)".format(len(generics.content)))
		return generics

	def __buildDeps(self, xml_deps):
		deps = Deps()
		if xml_deps:
			for xml_node in xml_deps:
				deps.content.append(xml_node.attrib['name'])

		log.info("buildDeps: built {0:d} dependenc(y/ies)".format(len(deps.content)))
		return deps

	def __buildParam(self, xml_node):
		param = Param()
		param.name = xml_node.attrib['name']
		param.type = xml_node.attrib['type']
		param.value = xml_node.attrib['val']

		log.info("buildParam: built param: " + str(param))
		return param

#class BackendConfigWriter - builds testbench configuration for component
class BackendConfigWriter:
	def __init__(self, meta, tb_file, vector_filename_len):
		self.meta = meta
		self.file = open(os.path.splitext(tb_file)[0].replace("_tb", "") + "_testing_config.vhd", "w")
		self.vector_filename_len = vector_filename_len

	def run(self):
		content = ""
		content += "package testing_config is\n"
		content += "\tconstant SIGNAL_COUNT : INTEGER := {0:d};\n".format(self.meta.signals.getFieldCount())
		content += "\tconstant TESTCASE_COUNT : INTEGER := {0:d};\n".format(self.meta.testcases.getTestcaseCount())
		content += "\tconstant FILENAME_LEN : INTEGER := {0:d};\n".format(self.vector_filename_len)
		content += "\tconstant CLOCK_PERIOD : TIME := {0:d} ns;\n".format(UT.TimeUtils.timeValueInNsFromTime(self.meta.component.interval))
		content += "end testing_config;\n"
		self.file.write(content)
		self.file.close()

# class BackendDepWriter - builds dependencies for VHDL project
class BackendDepWriter:
	def __init__(self, tb_file):
		self.file = open(os.path.splitext(tb_file)[0] + ".dep", "w")

	def run(self, deps):
		if deps:
			for dep in deps.content:
				self.file.write(dep + "\n")
		self.file.close()

# class BackendSimWriter - builds simulation specific description file
class BackendSimWriter:
# PUBLIC methods
	def __init__(self, meta, tb_file):
		self.meta = meta
		self.file = open(os.path.splitext(tb_file)[0] + ".cmd", "w")

	def insertHeader(self):
		self.file.write("onerror {resume}\n")

	def insertMarker(self, time):
		self.file.write("marker add {0:s}\n".format(time))
	
	def insertSignals(self):
		for signal_clock in self.meta.signals.list:
			if signal_clock.role == 'clock':
				self.__insertClock(signal_clock.name)

		self.__insertSection("INPUT-S", "in")
		self.__insertSection("OUTPUT-S", "out")
		self.__insertSection("BIDIR-S", "inout")

	def insertRunCommand(self, time):
		self.file.write("wave add -radix unsigned -color {0:s} -name TESTCASE_NO /TC_NUM\nrun {1:s}\nquit;\n"\
			.format(color_tc_num, time))

	def destroy(self):
		self.file.close();

# PRIVATE methods
	def __insertClock(self, name):
		self.file.write("wave add -color {1:s} -name {0:s} /s_{0:s}\n".format(name, color_clock))

	def __insertDivider(self, name, flag, color):
		if not flag:
			self.file.write("divider add -color dark{1:s} {0:s}\n".format(name, color))
		return True

	def __insertSection(self, name, role):
		has_section = False

		if role == 'in':
			color = color_input
		elif role == 'out':
			color = color_output
		else:
			color = color_bidir

		for signal in self.meta.signals.list:
			if signal.role == role:
				has_section = self.__insertDivider(name, has_section, color)
				self.__insertSignal(signal, color)

		for signal_vec in self.meta.signals.list:
			if signal_vec.role == (role + "_vec"):
				has_section = self.__insertDivider(name, has_section, color)
				self.__insertVector(signal_vec, color)

	def __insertSignal(self, signal, color):
		self.file.write("wave add -color {1:s} -name {0:s} {{/ports[{2:d}]}}\n".format(signal.name, color, signal.pos))

	def __insertGroup(self, signal):
		self.file.write("set group_{0:s}_{1:s}_id [group add {0:s}]\n"\
			.format(signal.name, signal.role))
	
	def __insertVector(self, signal, color):
		self.__insertGroup(signal)
		port_pos = 0
		i = signal.size - 1
		while i >= 0:
			if signal.ascending:
				port_pos = signal.pos + i
			else:
				port_pos = signal.pos + signal.size - i - 1
			port = "{{ports[{0:d}]}} ".format(port_pos)
			name = "{0:s}:{1:d}-ports:{2:d}".format(signal.name, i, port_pos)
			self.file.write("wave add {0:s} -color {4:s} -name {3:s} -into $group_{1:s}_{2:s}_id\n"\
				.format(port, signal.name, signal.role, name, color))
			i -= 1

# class TestWriter - builds test for given target (vhdl)
class TestWriter:
	def __init__(self, meta, file, vector_writer):
		self.meta = meta
		self.component = meta.component
		self.signals = meta.signals
		self.testcases = meta.testcases
		self.file = open(file, 'w')
		self.vectorWriter = vector_writer

		self.generics = meta.backend_data.generics
		self.deps = meta.backend_data.deps

		self.component_name = self.component.name
		self.tb_name = self.component_name + "_tb"
		self.testbench_duration = 0

		self.configWriter = BackendConfigWriter(meta, file, len(vector_writer.getTestVectorFileName(0)))
		self.simWriter = BackendSimWriter(meta, file)
		self.depWriter = BackendDepWriter(file)

# PUBLIC methods
	def run(self):
		self.simWriter.insertHeader()
		self.simWriter.insertSignals()

		self.__prepareLibraries()
		self.__prepareComponent()
		self.__prepareSignals()
		self.__prepareUut()
		self.__prepareClocks()
		self.__prepareStimProc()

		self.simWriter.insertRunCommand(self.getTestbenchDuration())
		self.depWriter.run(self.deps)
		self.configWriter.run()

		self.file.close()
		self.vectorWriter.generateDefaultVector()
		self.__generateMetaInfoFile()

	def getTestbenchDuration(self):
		return "{0:d} ns".format(self.testbench_duration)

# PRIVATE methods
	def __isGeneric(self):
		if not self.generics:
			return False
		if len(self.generics.content):
			return True
		return False

	def __getRange(self, pos, size, ascending):
		lower_bound = pos
		higher_bound = lower_bound + size - 1
		if ascending:
			range_str = "({0:d} to {1:d})".format(lower_bound, higher_bound)
		else:
			range_str = "({0:d} downto {1:d})".format(higher_bound, lower_bound)
		return range_str

	def __getMetaInfoFileName(self):
		return "{0:s}/{1:s}.mi".format(self.meta.getTestbenchDir(), self.component.name)

	def __getVectorTotalCount(self):
		cnt = 0
		gl = glob.glob("{0:s}/{1:s}_*.vec".format(self.meta.getTestbenchDir(), self.component.name))
		for v in gl:
			if not v.find("df.vec") == -1:
				gl.remove(v)
		gl.sort()
		for f in gl:
			vf = open(f)
			for l in vf.readlines():
				if not (l.startswith("#") or l == "\n"):
					cnt += 1

			vf.close()
		return cnt

	def __generateMetaInfoFile(self):
		mi_file_name = self.__getMetaInfoFileName()
		file = open(mi_file_name, 'w')
		if self.meta.component.type == 'concurrent':
			comp_type = 'c'
		else:
			comp_type = 's'
		file.write("t:{0:s};s:{1:d};t:{2:d};v:{3:d};{4:s};{5:s}"\
			.format(comp_type, self.meta.signals.count, self.meta.testcases.getTestcaseCount(),\
				self.__getVectorTotalCount(), self.meta.component.interval, self.meta.component.clk_period))
		file.close()

	def __prepareLibraries(self):
		self.file.write("library IEEE;\n")
		self.file.write("use IEEE.STD_LOGIC_1164.ALL;\n")
		self.file.write("use STD.TEXTIO.ALL;\n\n")
		self.file.write("use WORK.TESTING_CONFIG.ALL;\n")
		self.file.write("use WORK.TESTING_COMMON.ALL;\n")
		self.file.write("use WORK.TESTING.ALL;\n\n")

	def __prepareComponent(self):
		self.file.write("entity {0:s} is\nend {0:s};\n\n".format(self.tb_name))

		self.file.write("architecture behavior of {0:s} is\n".format(self.tb_name))
		self.__prepareComponentConstants()

		self.file.write("\t-- component\n\tcomponent {0:s}\n".format(self.component_name))
		if self.__isGeneric():
			self.__prepareComponentGenerics()
		self.__prepareComponentPort()
		self.file.write("\tend component;\n\n")

	def __prepareComponentConstants(self):
		self.file.write("\t-- constants\n")
		for clock in self.signals.list:
			if clock.role == 'clock':
				self.file.write("\tconstant DEF_{0:s}_VAL : STD_LOGIC := '{1:s}';\n"\
					.format(clock.name.upper(), clock.value))
		self.file.write("\n")
		if self.__isGeneric():
			self.file.write("\t-- generics\n")
			for param in self.generics.content:
				self.file.write("\tconstant GENERIC_PARM_{0:s} : {1:s} := {2:s};\n"\
					.format(param.name, param.type, param.value))
			self.file.write("\n")

	def __prepareComponentGenerics(self):
		self.file.write("\tgeneric (\n")

		generics_count = len(self.generics.content)
		for generic in range(generics_count - 1):
			param = self.generics.content[generic]
			self.file.write("\t\t{0:s} : {1:s};\n".format(param.name, param.type))
		param = self.generics.content[generics_count - 1]
		self.file.write("\t\t{0:s} : {1:s}\n".format(param.name, param.type))

		self.file.write("\t);\n")

	def __prepareComponentPort(self):
		self.file.write("\tport (\n")
		signal_count = len(self.signals.list)
		for signal_num in range(signal_count - 1):
			signal = self.signals.list[signal_num]
			if type(signal) is CLS.SignalVector:
				self.__prepareComponentPortVector(signal, False)
			else:
				self.__prepareComponentPortIO(signal, False)
			self.file.write("\n")

		signal = self.signals.list[signal_count - 1]
		if type(signal) is CLS.SignalVector:
			self.__prepareComponentPortVector(signal, True)
		else:
			self.__prepareComponentPortIO(signal, True)
		self.file.write("\n\t);\n")

	def __prepareComponentPortIO(self, signal, end):
		role = signal.role
		if role == 'clock':
			role = 'in'
		content = "\t\t{0:s} : {1:s} {2:s}".format(signal.name, role, signal.type)
		if not end:
			content += ";"
		self.file.write(content)

	def __prepareComponentPortVector(self, signal, end):
		if signal.ascending:
			range_str = "(0 to {0:d})".format(int(signal.size) - 1)
		else:
			range_str = "({0:d} downto 0)".format(int(signal.size) - 1)
		content = "\t\t{0:s} : {1:s} {2:s} {3:s}"\
			.format(signal.name, signal.role.replace('_vec', ''), signal.type, range_str)
		if not end:
			content += ";"
		self.file.write(content)

	def __prepareSignals(self):
		self.file.write("\t-- signal vector\n\tsignal ports : STD_LOGIC_VECTOR (0 to (SIGNAL_COUNT-1)) := (others => '0');\n")
		self.file.write("\n\t-- test indication\n\tsignal TC_NUM : INTEGER := 0;\n")
		prev_signal_role = ""
		for signal in self.signals.list:
			if signal.role != prev_signal_role:
				self.file.write("\n\t-- {0:s}-s\n".format(signal.role))
			if signal.role == "clock":
				self.__prepareSignalsClock(signal)
			elif type(signal) is CLS.SignalVector:
				self.__prepareSingalsVector(signal)
			else:
				self.__prepareSignalsIO(signal)
			prev_signal_role = signal.role

	def __prepareSignalsClock(self, signal):
		self.file.write("\tsignal s_{0:s} : {1:s} := {2:s};\n"\
			.format(signal.name, signal.type, "DEF_{0:s}_VAL".format(signal.name.upper())))
		self.file.write("\tsignal s_{0:s}_rst : STD_LOGIC := '0';\n".format(signal.name))

	def __prepareSignalsIO(self, signal):
		self.file.write("\talias s_{0:s} : {1:s} is ports({2:d});\n"\
			.format(signal.name, signal.type, signal.pos))

	def __prepareSingalsVector(self, signal):
		range_str = self.__getRange(signal.pos, signal.size, True)
		self.file.write("\talias s_{0:s} : {1:s} is ports {2:s};\n"\
			.format(signal.name, signal.type, range_str))

	def __prepareUut(self):
		self.file.write("\nbegin\n\t-- unit under test\n\tuut: entity work.{0:s}\n".format(self.component_name))
		if self.__isGeneric():
			self.__prepareGenericMap()
		self.__preparePortMap()

	def __preparePortMap(self):
		self.file.write("\tport map(\n")

		signal_count = len(self.signals.list)
		for signal_num in range(signal_count - 1):
			signal = self.signals.list[signal_num]
			self.file.write("\t\t{0:s} => s_{0:s},\n".format(signal.name))
		signal = self.signals.list[signal_count - 1]
		self.file.write("\t\t{0:s} => s_{0:s}\n".format(signal.name))
		self.file.write("\t);\n\n")

	def __prepareGenericMap(self):
		self.file.write("\tgeneric map(\n")

		generic_count = len(self.generics.content)
		for generic_num in range(generic_count - 1):
			param = self.generics.content[generic_num]
			self.file.write("\t\t{0:s} => GENERIC_PARM_{0:s},\n".format(param.name))
		param = self.generics.content[generic_count - 1]
		self.file.write("\t\t{0:s} => GENERIC_PARM_{0:s}\n".format(param.name))
		self.file.write("\t)\n")

	def __prepareClocks(self):
		self.file.write("\t-- clock processes\n")
		if self.component.type == 'concurrent':
			self.file.write("\t-- NONE")
		else:
			for signal in self.signals.list:
				if signal.role == "clock":
					self.__prepareClockProcess(signal)

	def __prepareClockProcess(self, clock):
		self.file.write("\t-- clock: {0:s}\n".format(clock.name))
		self.file.write("\t{0:s}_clock_proc: process (s_{0:s}, s_{0:s}_rst)\n\tbegin\n".format(clock.name))
		self.file.write("\t\tif s_{0:s}_rst = '0' then\n\t\t\ts_{0:s} <= not s_{0:s} after ({1:s} / 2);\n\t\telse\n\t\t\ts_{0:s} <= DEF_{2:s}_VAL;\n"\
			.format(clock.name, clock.getPeriod(), clock.name.upper()))
		self.file.write("\t\tend if;\n\tend process;")
			
		self.file.write("\n")

	def __prepareStimProc(self):
		self.file.write("\n\t-- stimulus process\n\tstim_proc: process\n")
		self.file.write("\t\tfile vector_file : TEXT;\n")
		self.file.write("\t\tvariable eof : BOOLEAN;\n")
		self.file.write("\t\tvariable def_set_vector : STD_LOGIC_VECTOR ((SIGNAL_COUNT-1) downto 0) := (others => '-');\n")
		self.file.write("\t\tvariable set_vector : STD_LOGIC_VECTOR ((SIGNAL_COUNT-1) downto 0);\n")
		self.file.write("\t\tvariable expect_vector : STD_LOGIC_VECTOR ((SIGNAL_COUNT-1) downto 0);\n")
		self.file.write("\t\tvariable vector_num : INTEGER := 0;\n")
		self.file.write("\t\tvariable fail : BOOLEAN := false;\n")
		self.file.write("\t\tvariable failed_vectors : INTEGER := 0;\n")
		self.file.write("\t\tvariable tb_fail_count : INTEGER := 0;\n")
		self.file.write("\t\tvariable vector_interval : TIME;\n")
		self.file.write("\n")
		self.file.write("\t\tvariable filename_array : T_FILENAME;\n")
		self.file.write("\t\tvariable testname_array : T_TESTNAME;\n")
		self.file.write("\t\tvariable teststate_array : T_TESTSTATE;\n")
		for signal in self.signals.list:
			if signal.role == 'clock':
				self.file.write("\t\tvariable {0:s}_rst_dis : T_CLOCK_RESET_DISABLE;\n".format(signal.name))

		self.file.write("\tbegin\n")
		self.file.write("\t\t-- insert testcase names\n")
		testname_entry = 1
		for test in self.testcases.list:
			name = test.name
			name += ' ' * (128 - len(test.name))
			self.file.write("\t\ttestname_array({0:d}) := \"{1:s}\";\n".format(testname_entry, name))
			testname_entry += 1
		self.file.write("\n")

		testname_entry = 1
		self.file.write("\t\t-- insert testcase states\n")
		for test in self.testcases.list:
			if test.rememberState == False:
				self.file.write("\t\tteststate_array({0:d}) := TS_DISCARD;\n".format(testname_entry))
			else:
				self.file.write("\t\tteststate_array({0:d}) := TS_REMEMBER;\n".format(testname_entry))
			testname_entry += 1
		self.file.write("\n")

		if self.signals.getClockCount() != 0:
			self.file.write("\t\t-- insert clock configuration\n")
			clock_num = 1
			for test in self.testcases.list:
				if test.clock_reset and test.clock_disable:
					log.error("prepareStimProc: clock_reset and clock_disable cannot be defined in single testcase")
				clock_reset = test.clock_reset
				clock_disable = test.clock_disable
				if clock_reset:
					self.file.write("\t\t{0:s}_rst_dis({1:d}) := CLK_RESET;\n".format(clock_reset, clock_num))
				elif clock_disable:
					self.file.write("\t\t{0:s}_rst_dis({1:d}) := CLK_DISABLE;\n".format(clock_disable, clock_num))
				else:
					self.file.write("\t\t{0:s}_rst_dis({1:d}) := CLK_DEFAULT;\n".format(self.signals.getClock(), clock_num))
				clock_num += 1
			self.file.write("\n")

		self.file.write("\t\t-- setting defaults\n")
		for signal in self.signals.list:
			if signal.value and signal.role != 'clock':
				if type(signal) is CLS.SignalVector:
					range_str = self.__getRange(signal.pos, signal.size, False)
					self.file.write("\t\tdef_set_vector{0:s} := \"{1:s}\";\n"\
						.format(range_str, signal.value))
				else:
					self.file.write("\t\tdef_set_vector({0:d}) := '{1:s}';\n"\
						.format(signal.pos, signal.value))
		self.file.write("\n")

		self.file.write("\t\t-- build vector filenames array\n")
		vector_file_name_short = os.path.dirname(self.vectorWriter.getTestVectorFileName(0)) + "/"
		self.file.write("\t\ttb_build_filename_array(\"{0:s}\", \"{1:s}\", filename_array);\n"
			.format(vector_file_name_short, self.component.name))
		
		self.file.write("\t\t-- wait for circuit initialization\n\t\twait for 1 ns;\n")
		self.file.write("\n\t\t-- TESTBENCH ENTRY\n\t\ttb_begin;\n\n")
		self.file.write("\t\tfor testcase_num in 1 to TESTCASE_COUNT loop\n")
		if self.signals.getClockCount() != 0:
			self.file.write("\t\t\t-- main clock handling\n")
			self.file.write("\t\t\tcase clk_rst_dis(testcase_num) is\n")
			self.file.write("\t\t\t\twhen CLK_RESET =>\n")
			self.file.write("\t\t\t\t\treport \"RESETTING CLOCK: {0:s}\";\n".format(self.signals.getClock()))
			self.file.write("\t\t\t\t\tTC_NUM  <= 128;\n")
			self.file.write("\t\t\t\t\ts_clk_rst <= '1';\n")
			self.file.write("\t\t\t\t\twait for CLOCK_PERIOD;\n")
			self.file.write("\t\t\t\t\ts_clk_rst <= '0';\n")
			self.file.write("\t\t\t\t\twait for 1 ns;\n")
			self.file.write("\t\t\t\twhen CLK_DISABLE =>\n")
			self.file.write("\t\t\t\t\treport \"DISABLING CLOCK: {0:s}\";\n".format(self.signals.getClock()))
			self.file.write("\t\t\t\t\ts_clk_rst <= '1';\n")
			self.file.write("\t\t\t\twhen others =>\n")
			self.file.write("\t\t\t\t\ts_clk_rst <= '0';\n")
			self.file.write("\t\t\tend case;\n\n")

		self.file.write("\t\t\ttb_tc_header(testname_array, testcase_num);\n")
		self.file.write("\t\t\tfailed_vectors := 0;\n\n")
		self.file.write("\t\t\tTC_NUM <= testcase_num;\n\n")
		self.file.write("\t\t\tinit_set_vector(def_set_vector, teststate_array(testcase_num), set_vector);\n")
		self.file.write("\t\t\tvector_file_open(filename_array(testcase_num), vector_file);\n\n")
		self.file.write("\t\t\tvector_num := 1;\n")
		self.file.write("\t\t\tloop\n")
		self.file.write("\t\t\t\tfill_vectors_from_file(vector_file, vector_num, set_vector, expect_vector, eof, vector_interval);\n")
		self.file.write("\t\t\t\texit when eof = true;\n\n")
		self.file.write("\t\t\t\tports <= set_ports(set_vector);\n")
		self.file.write("\t\t\t\twait for vector_interval;\n\n")
		self.file.write("\t\t\t\tcheck_expectations(expect_vector, ports, testcase_num, vector_num, fail);\n")
		self.file.write("\t\t\t\tif fail = true then\n")
		self.file.write("\t\t\t\t\tfailed_vectors := failed_vectors + 1;\n")
		self.file.write("\t\t\t\tend if;\n")
		self.file.write("\t\t\t\tvector_num := vector_num + 1;\n")
		self.file.write("\t\t\tend loop;\n\t\t\tfile_close(vector_file);\n");
		self.file.write("\t\t\ttb_tc_footer(failed_vectors);\n")
		self.file.write("\t\t\tif failed_vectors > 0 then\n")
		self.file.write("\t\t\t\ttb_fail_count := tb_fail_count + 1;\n")
		self.file.write("\t\t\tend if;\n")
		self.file.write("\t\tend loop;\n\n")

		test_count = len(self.testcases.list)

		for test_num in range(test_count):
			test_number = test_num + 1

			test = self.testcases.list[test_num]
			testcase_duration =  self.vectorWriter.generateVector(test_number, test)
			self.testbench_duration += testcase_duration

			if test.clock_reset:
				self.testbench_duration += UT.TimeUtils.timeValueInNsFromTime(self.component.interval) + 1

			marker = "{0:d} ns".format(self.testbench_duration + 1)
			self.simWriter.insertMarker(marker)

		self.testbench_duration += UT.TimeUtils.timeValueInNsFromTime(self.component.interval)


		duration = str(self.testbench_duration) + " ns"
		self.file.write("\t\t-- TESTBENCH END\n\t\ttb_end(tb_fail_count);\n\t\tTC_NUM <= 255;\n")
		self.file.write("\t\twait;\n\n")
		self.file.write("\t\t-- TIME DURATION: {0:s}\n".format(duration))
		self.file.write("\tend process;\nend;\n")
