import os

import log
import Classes as CLS
import Utils as UT

# VectorWriter class - builds vector files for testbenches
class VectorWriter:
	def __init__(self, meta, out, scripts):
		self.tc_dir = ""
		if os.path.isabs(out):
			self.tc_dir = os.path.dirname(out)
		else:
			self.tc_dir = "{0:s}/{1:s}".format(os.getcwd(), os.path.dirname(out))
		self.tc_dir = os.path.realpath(self.tc_dir)

		self.component = meta.component
		self.signals = meta.signals
		self.scripts_dir = scripts
		self.header = self.__buildHeader()

# PUBLIC methods
	def generateVector(self, test_num, test):
		file_name = self.getTestVectorFileName(test_num)
		field_count = self.signals.getFieldCount()
		time_duration = 0

		log.info("generateVector: " + file_name)
		self.file = open(file_name, 'w')
		self.file.write("#{0:s}\n".format(test.name))
		self.file.write(self.header)

		for command in test.content:
			if type(command) is CLS.TestStep:
				field = 0
				self.file.write(" {0:s}".format(command.after))
				while field < field_count:
					signal = self.signals.getSignalAtPosition(field)
					self.file.write(" ")

					if type(signal) == CLS.SignalVector:
						self.__generateVectorWriteVector(signal, command)
					elif type(signal) == CLS.Signal:
						self.__generateVectorWriteSignal(signal, command)
					else:
						log.error("generateVector: unexpected signal type")
					field += signal.size
				self.file.write("\n")
				time_duration += UT.TimeUtils.timeValueInNsFromInterval(command.after)
			elif type(command) is CLS.TestSequence:
				for entry in command.list:
					time_duration += UT.TimeUtils.timeValueInNsFromInterval(self.__getIntervalFromSequenceVector(entry))
					self.file.write(" {0:s}\n".format(entry))
			elif type(command) is CLS.TestScript:
				TS = __import__(self.__getScriptFile(command.file))
				log.info("generateVector: running script: " + self.component.name + "_" + command.file)
				res_time_duration, res_content = TS.process(self.component)
				time_duration += res_time_duration
				self.file.write(res_content)
			else:
				log.error("invalid test command found")

		self.file.close()
		return time_duration

	def generateDefaultVector(self):
		file_name = self.getTestDefaultVectorFileName()

		log.info("generateDefaultVector: " + file_name)
		file = open(file_name, 'w')
		file.write(self.header)

		file.write("     ")
		for signal in self.signals.list:
			if signal.role != 'clock':
				file.write(" ")

				if type(signal) is CLS.SignalVector:
					if signal.role == 'out':
						for pos in range(signal.size):
							value += '-'
					else:
						value = signal.value
					file.write("{0:s}".format(value))
				elif type(signal) == CLS.Signal:
					if signal.role == 'out':
						value = '-'
					else:
						value = signal.value
					file.write("{0:s}".format(value))
				else:
					log.error("generateDefaultVector: unexpected signal type")

		self.file.close()

	def getTestVectorFileName(self, number):
		return "{0:s}/{1:s}_{2:02d}.vec".format(self.tc_dir, self.component.name, number)

	def getTestDefaultVectorFileName(self):
		return "{0:s}/{1:s}_df.vec".format(self.tc_dir, self.component.name)

# PRIVATE methods
	def __buildHeader(self):
		header = ""
		name = ""
		line = 0
		max_length = self.__getSignalNameMaxLength()
		field_count = self.signals.getFieldCount()

		while line < max_length:
			header += "#time "
			field = 0

			while field < field_count:
				signal = self.signals.getSignalAtPosition(field)
				name = signal.name
				name_length = len(name)
				header += self.__buildHeaderGetSignalLetter(name, line, name_length, max_length)
				header += self.__buildFiller(signal.size, " ")
				field += signal.size
			header += "\n"
			line += 1
		return header

	def __getScriptFile(self, file):
		script_file = self.component.name + "_" + file
		return script_file

	def __getIntervalFromSequenceVector(self, value):
		return value[0:4]

	def __buildHeaderGetSignalLetter(self, name, line, name_length, max_length):
		if max_length - line > name_length:
			ret = " "
		else:
			ret = name[line - (max_length - name_length)]
		return ret

	def __buildFiller(self, size, fill_char):
		ret = ""
		for i in range(size):
			ret += fill_char
		return ret

	def __generateVectorWriteSignal(self, signal, command):
		if signal.role == 'in':
			self.file.write(command.set_list.get(signal.name, '-'))
		elif signal.role == 'out':
			self.file.write(command.expect_list.get(signal.name, '-'))
		elif signal.role == 'inout':
			if command.set_list.get(signal.name, ""):
				self.file.write(command.set_list.get(signal.name, '-'))
			elif command.expect_list.get(signal.name, ""):
				self.file.write(command.expect_list.get(signal.name, '-'))
			else:
				self.file.write('-')

	def __generateVectorWriteVector(self, signal, command):
		dc = self.__buildFiller(signal.size, "-")

		if signal.role == 'in_vec':
			self.file.write(command.set_list.get(signal.name, dc))
		elif signal.role == 'out_vec':
			self.file.write(command.expect_list.get(signal.name, dc))
		elif signal.role == 'inout_vec':
			if command.set_list.get(signal.name, ""):
				self.file.write(command.set_list.get(signal.name, dc))
			elif command.expect_list.get(signal.name, ""):
				self.file.write(command.expect_list.get(signal.name, dc))
			else:
				self.file.write(dc)

	def __getSignalNameMaxLength(self):
		max_length = 0
		for signal in self.signals.list:
			name_length = len(signal.name)
			if name_length > max_length:
				max_length = name_length
		return max_length
