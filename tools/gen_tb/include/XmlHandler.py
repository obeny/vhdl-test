import xml.etree.cElementTree as ET

import log
import Classes as CLS
import Utils as UT

#
# DEFINITIONS
# ===========
signal_types = ('clock', 'in', 'in_vec', 'out', 'out_vec', 'inout', 'inout_vec')

input_signals = ('in', 'in_vec', 'inout', 'inout_vec')
output_signals = ('out', 'out_vec', 'inout', 'inout_vec')

io_signal_default_type = 'STD_LOGIC'
io_vector_default_type = 'STD_LOGIC_VECTOR'

#
# CLASSES
# =======

# XmlHandler class - processes XML, checks its validity and builds internal representation
class XmlHandler:
# PUBLIC methods
	def __init__(self, xml, backend_handler):
		self.dom_root = ET.parse(xml).getroot()
		self.meta = None
		self.backendHandler = backend_handler
		self.current_pos = 0

	def buildMeta(self, out_dir):
		self.meta = CLS.Meta()
		self.meta.signals = self.__buildSignals()
		self.meta.component = self.__buildComponent()
		self.meta.testcases = self.__buildTestcases()
		self.meta.backend_data = self.backendHandler.buildData(self.dom_root.find('backends'))
		self.meta.out_dir = out_dir

		# do some sanity checks not covered by XSD
		self.__sanityCheck(self.meta)

		return self.meta

# PRIVATE methods
	def __sanityCheck(self, meta):
		log.info("sanityCheck: validating")
		header = "SANITY CHECK FAILED: "
		if not self.__sanityCheckClocks(meta):
			log.error(header + "no clocks defined for sequential component")
		if not self.__sanityCheckCountIO(meta):
			log.error(header + "component have to define at least one input and output")
		if not self.__sanityCheckVectorLength(meta):
			log.error(header + "test vector length is incorrect")
		if not self.__sanityCheckValues(meta):
			log.error(header + "incorrect values fed to pin")

	def __sanityCheckClocks(self, meta):
		if meta.component.type == 'sequential':
			for signal in meta.signals.list:
				if signal.role == 'clock':
					return True
			return False
		else:
			return True

	def __sanityCheckCountIO(self, meta):
		input_count = 0
		output_count = 0
		for signal in meta.signals.list:
			if signal.role in input_signals:
				input_count += 1
			if signal.role in output_signals:
				output_count += 1

		if input_count > 0 and output_count > 0:
			return True
		return False

	def __sanityCheckValues(self, meta):
		for testcase in meta.testcases.list:
			for test_entry in testcase.content:
				if type(test_entry) is CLS.TestStep:
					# set is handled in schema, take care of expect only
					expect_list = test_entry.expect_list
					for expect_entry in expect_list:
						if meta.signals.getSignal(expect_entry).role == "out":
							if expect_list[expect_entry] not in ("h", "l", "-"):
								log.error("sanityCheckValues: TestStep out={0:s} expect is not ('h', 'l', '-'), got={1:s}"
									.format(expect_entry, expect_list[expect_entry]))
						elif meta.signals.getSignal(expect_entry).role == "out_vec":
							for value_pos in range(0, len(expect_list[expect_entry])):
								if expect_list[expect_entry][value_pos] not in ("h", "l", "-"):
									log.error("sanityCheckVallues: TestStep out_vec[{0:d}]={1:s} expect is not ('h', 'l', '-'), got={2:s}"
										.format(value_pos, expect_entry, expect_list[expect_entry][value_pos]))

						elif meta.signals.getSignal(expect_entry).role == "inout":
							if expect_list[expect_entry] not in ("Z", "H", "L", "-", "h", "l", "X"):
								log.error("sanityCheckValues: TestStep inout={0:s} expect is not ('Z', 'H', 'L', '-', 'h', 'l', 'X'), got={1:s}"
									.format(expect_entry, expect_list[expect_entry]))
						elif meta.signals.getSignal(expect_entry).role == "inout_vec":
							for value_pos in range(0, len(expect_list[expect_entry])):
								if expect_list[expect_entry][value_pos] not in ("Z", "H", "L", "-", "h", "l", "X"):
									log.error("sanityCheckVallues: TestStep inout_vec[{0:d}]={1:s} expect is not ('Z', H', 'L', '-', 'h', 'l', 'X'), got={2:s}"
										.format(value_pos, expect_entry, expect_list[expect_entry][value_pos]))
				elif type(test_entry) is CLS.TestSequence:
					vector_list = test_entry.list
					for value in vector_list:
						vector = value[len("#### "):].replace(" ", "")
						for pos in range(0, len(vector)):
							signal = meta.signals.getSignalAtPosition(pos)
							if signal.role.startswith("inout"):
								# no way to distinguish between set and exp
								if vector[pos] not in ("H", "L", "-", "0", "1", "Z", "l", "h", "X"):
									log.error("sanityCheckValues: TestSequence {0:s}={1:s} expect is not ('H', 'L', '-', '0', '1', 'Z', 'l', 'h', 'X'), got={2:s}"
										.format(signal.role, signal.name, vector[pos]))
				elif type(test_entry) is CLS.TestScript:
					log.note("sanityCheckValues: no validation for script test available")
				else:
					# should be handeld by schema, but...
					log.error("sanityCheckValues: invalid test type")
		return True

	def __sanityCheckVectorLength(self, meta):
		for testcase in meta.testcases.list:
			step = 1
			for test_entry in testcase.content:
				if type(test_entry) is CLS.TestStep:
					set_list = test_entry.set_list
					expect_list = test_entry.expect_list
					if self.__sanityCheckVectorLengthInStepList(meta, set_list, step) == False:
						return False
					if self.__sanityCheckVectorLengthInStepList(meta, expect_list, step) == False:
						return False;
				elif type(test_entry) is CLS.TestSequence:
					vector_list = test_entry.list
					for vector in vector_list:
						vector = vector[5:]
						signals = vector.split(" ")
						pos = 0
						for signal_val in signals:
							meta_signal = meta.signals.getSignalAtPosition(pos)
							if len(signal_val) != meta_signal.size:
								log.fatal("sanityCheckVectorLength: signal={0:s} with value={1:s} in step={2:d} has incorrect length"
									.format(meta_signal.name, signal_val, step))
								return False
							pos += meta_signal.size

				step += 1
		return True

	def __sanityCheckVectorLengthInStepList(self, meta, sig_list, step):
		for entry in sig_list:
			signal = meta.signals.getSignal(entry)
			if signal.role.endswith("_vec"):
				if len(sig_list[entry]) != signal.size:
					log.fatal("sanityCheckVectorLength: signal={0:s} with value={1:s} in step={2:d} has incorrect length"
						.format(entry, sig_list[entry], step))
					return False
		return True

	def __buildComponent(self):
		xml_component = self.dom_root.find('component')
		component = CLS.Component()

		component.name = xml_component.attrib['name']
		component.type = xml_component.attrib['type']
		component.interval = xml_component.attrib['interval']
		component.clk_period = self.meta.signals.getSignal(self.meta.signals.getClock()).freq

		log.info("buildComponent: built component " + str(component))
		return component

	def __buildSignals(self):
		xml_signals = self.dom_root.find('signals')
		signals = CLS.SignalContainer()

		for xml_signal in list(xml_signals):
			if xml_signal.tag in signal_types:
				signal = self.__buildSignal(xml_signal)
				if not signals.insertSignal(signal):
					log.error("buildSignals: duplicated signal name: " + xml_signal.tag)
			else:
				log.error("buildSignals: unknown signal defined: " + xml_signal.tag)

		log.info("buildSignals: defined {0:d} signal(s) with {1:d} slot(s)"\
			.format(len(signals.list), signals.getFieldCount()))
		return signals

	def __buildSignal(self, xml_node):
		if xml_node.tag in CLS.io_signals:
			signal = self.__buildSignalIO(xml_node)
		elif xml_node.tag in CLS.io_vectors:
			signal = self.__buildSignalVector(xml_node)
		elif xml_node.tag == 'clock':
			signal = self.__buildSignalClock(xml_node)
		else:
			log.error("buildSignal: invalid signal definition: " + xml_node.tag)

		log.info("buildSignal: built signal " + str(signal))
		return signal

	def __buildSignalIO(self, xml_node):
		signal = CLS.Signal()
		signal.size = 1
		signal.pos = self.current_pos

		signal.name = XmlHandlerHelper.signalGetName(xml_node)
		signal.role = XmlHandlerHelper.signalGetRole(xml_node)
		signal.type = XmlHandlerHelper.signalGetType(xml_node)
		
		signal.value = xml_node.attrib.get('val', '')
		self.current_pos += signal.size
		return signal

	def __buildSignalClock(self, xml_node):
		signal = CLS.SignalClock()
		signal.name = XmlHandlerHelper.signalGetName(xml_node)
		signal.role = XmlHandlerHelper.signalGetRole(xml_node)
		signal.type = XmlHandlerHelper.signalGetType(xml_node)

		signal.value = xml_node.attrib.get('val', '0')
		signal.freq = xml_node.attrib['freq']
		return signal

	def __buildSignalVector(self, xml_node):
		signal = CLS.SignalVector()
		signal.size = int(xml_node.attrib['size'])
		signal.pos = self.current_pos

		signal.name = XmlHandlerHelper.signalGetName(xml_node)
		signal.role = XmlHandlerHelper.signalGetRole(xml_node)
		signal.type = XmlHandlerHelper.signalGetType(xml_node)

		signal.ascending = xml_node.attrib['order'] == "asc"
		signal.value = xml_node.attrib.get('val', '').replace(" ", "")
		self.current_pos += signal.size
		return signal

	def __buildTestcases(self):
		xml_testcases = self.dom_root.find('testcases')
		testcases = CLS.TestcaseContainer()
		
		for xml_testcase in xml_testcases.findall('test'):
			test = self.__buildTest(xml_testcase)
			if test:
				testcases.insertTestcase(test)

		log.info("buildTestcases: built {0:d} testcase(s)".format(testcases.getTestcaseCount()))
		return testcases

	def __buildTest(self, xml_node):
		test = CLS.Test()
		test.name = XmlHandlerHelper.testGetName(xml_node)
		test.rememberState = XmlHandlerHelper.testGetStateInfo(xml_node)
		test.clock_reset = XmlHandlerHelper.testGetClockReset(xml_node)
		test.clock_disable = XmlHandlerHelper.testGetClockDisable(xml_node)
		test.disabled = XmlHandlerHelper.testGetDisabled(xml_node)

		if test.disabled:
			log.info("buildTest: test disabled: " + test.name)
			return None

		for command in list(xml_node):
			test_entry = None
			if command.tag == 'step':
				test_entry = self.__buildTestStep(command)
			elif command.tag == 'seq':
				test_entry = self.__buildTestSequence(command)
			elif command.tag == 'script':
				test_entry = self.__buildTestScript(command)
			else:
				log.error("buildTest: unexpected test command found: " + command.tag)
			test.content.append(test_entry)

		log.info("builtTest: built test: " + test.name)
		return test

	def __buildTestSequence(self, xml_node):
		sequence = CLS.TestSequence()
		cmds = xml_node.findall('vec')
		for cmd in cmds:
			value = cmd.text
			if value[0:4] == '####':
				interval = UT.TimeUtils.timeToInterval(self.meta.component.interval)
				value = value.replace('####', interval)
				log.note("buildTestSequence: no interval defined, defaulting to: \'" + interval + "\'")
			sequence.list.append(value)
			log.info("buildTestSequence: built sequence step with values: \'" + value + "\'")
		return sequence

	def __buildTestStep(self, xml_node):
		step = CLS.TestStep()
		for item in list(xml_node):
			if item.tag.startswith('set'):
				self.__fillTestStepSet(item, step)
			elif item.tag.startswith('exp'):
				self.__fillTestStepExpect(item, step)
		after = xml_node.attrib.get('after', '')
		if not after:
			step.after = UT.TimeUtils.timeToInterval(self.meta.component.interval)
		else:
			step.after = after

		log.info("buildTestStep: built test step with wait interval: \'" + step.after + "\'")
		return step

	def __buildTestScript(self, xml_node):
		script = CLS.TestScript()
		script.file = xml_node.attrib['file']
		log.info("buildTestScript: built test with script file: \'" + script.file + "\'")
		return script

	def __fillTestStepSet(self, xml_node, step):
		name = xml_node.attrib['sig']
		if not self.meta.signals.getSignal(name):
			log.error("fillTestStepSet: signal=\'{0:s}\' doesn't exist".format(name))
		value = xml_node.attrib['val'].replace(" ", "")
		step.set_list[name] = value
		log.info("fillTestStepSet: built step for signal={0:s} with value={1:s}".format(name, value))

	def __fillTestStepExpect(self, xml_node, step):
		name = xml_node.attrib['sig']
		if not self.meta.signals.getSignal(name):
			log.error("fillTestStepExpect: signal=\'{0:s}\' doesn't exist".format(name))
		value = xml_node.attrib['val'].replace(" ", "")
		step.expect_list[name] = value
		log.info("fillTestStepExpect: built step for signal={0:s} with value={1:s}".format(name, value))

# XmlHandlerHelper static class - simplifies access to xml nodes for XmlHandler
class XmlHandlerHelper:
	# SIGNAL
	@staticmethod
	def signalGetName(xml_node):
		return xml_node.attrib['name']

	@staticmethod
	def signalGetRole(xml_node):
		return xml_node.tag

	@staticmethod
	def signalGetType(xml_node):
		ret = xml_node.attrib.get('type', '')
		if not ret:
			if xml_node.tag.endswith('_vec'):
				signal_type = io_vector_default_type
			else:
				signal_type = io_signal_default_type
			log.note("getType: no type defined, defaulting to: " + signal_type)
			ret = signal_type
		return ret

	# TEST
	@staticmethod
	def testGetName(xml_node):
		return xml_node.attrib['name']

	@staticmethod
	def testGetStateInfo(xml_node):
		ret = False
		rememberState = xml_node.attrib.get('state', '')
		if rememberState == "remember":
			ret = True
		return ret

	@staticmethod
	def testGetClockReset(xml_node):
		return xml_node.attrib.get('clock_reset', '')

	@staticmethod
	def testGetClockDisable(xml_node):
		return xml_node.attrib.get('clock_disable', '')

	@staticmethod
	def testGetDisabled(xml_node):
		return xml_node.attrib.get('disabled', '')
