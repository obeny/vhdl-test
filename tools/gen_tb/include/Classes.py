import os

#
# GLOBAL DEFINITIONS
# ===========
io_signals = ('in', 'out', 'inout')
io_vectors = ('in_vec', 'out_vec', 'inout_vec')

#
# SINGLETONS
# ==========

# META information about test and backend
class Meta:
	component = None
	signals = None
	testcases = None
	backend_data = None
	out_dir = None

	def getTestbenchDir(self):
		tb_dir = ""
		if os.path.isabs(self.out_dir):
			tb_dir = os.path.dirname(self.out_dir)
		else:
			tb_dir = "{0:s}/{1:s}".format(os.getcwd(), os.path.dirname(self.out_dir))
		tb_dir = os.path.realpath(tb_dir)
		return tb_dir

# COMPONENT information
class Component:
	name = ""
	type = ""
	interval = ""

	def __str__(self):
		return "name={0:s}, type={1:s}, interval={2:s}"\
			.format(self.name, self.type, self.interval)

# SIGNALS information
class SignalContainer:
	list = []
	count = 0
	clocks = -1

	def insertSignal(self, new_signal):
		for signal in self.list:
			if signal.name == new_signal.name:
				return None
		self.list.append(new_signal)
		return new_signal

	def getClock(self):
		for signal in self.list:
			if signal.role == 'clock':
				return signal.name

		return None

	def getClockCount(self):
		if self.clocks != -1:
			return self.clocks

		self.clocks = 0
		for signal in self.list:
			if signal.role == 'clock':
				self.clocks += 1
		return self.clocks

	def getFieldCount(self):
		if self.count != 0:
			return self.count

		for signal in self.list:
			if signal.role in io_vectors:
				self.count += int(signal.size)
			elif signal.role in io_signals:
				self.count += 1
		return self.count

	def getSignalAtPosition(self, pos):
		ret = None
		for signal in self.list:
			if pos >= signal.pos and pos <(signal.pos + signal.size):
				ret = signal
				break
		return ret

	def getSignal(self, name):
		for signal in self.list:
			if signal.name == name:
				return signal
		return None

# TESTCASES information
class TestcaseContainer:
	list = []
	longest_name = 0

	def insertTestcase(self, new_test):
		self.list.append(new_test)

	def getTestcaseCount(self):
		return len(self.list)

	def getTestcaseName(self):
		return self.list.name

#
# INSTANTIATED
# ============

# SIGNAL base class
class Signal:
	def __init__(self):
		self.size = 0
		self.pos = -1

		self.name = ""
		self.role = ""
		self.type = ""
		self.value = ""

	def __str__(self):
		ret = "name={0:s}, role={1:s}, type={2:s}, pos={3:d}, size={4:d}"\
			.format(self.name, self.role, self.type, self.pos, self.size)
		if self.role != 'out':
			ret += ", value={0:s}".format(self.value)

		return ret

# SIGNAL clock
class SignalClock(Signal):
	def __init__(self):
		Signal.__init__(self)
		self.freq = ""
		self.period = ""

	def __str__(self):
		return "name={0:s}, role={1:s}, type={2:s}, value={3:s}, freq={4:s}"\
			.format(self.name, self.role, self.type, self.value, self.freq)

	def getPeriod(self):
		if not self.period:
			value = int(self.freq.split(" ")[0])
			suffix = self.freq.split(" ")[1]

			period_value = 1000.0/value
			if suffix == 'k':
				period_suffix = "us"
			elif suffix == "M":
				period_suffix = "ns"
			elif suffix == "G":
				period_suffix = "ps"
			else:
				log.error("getPeriod: unsupported frequency")

			self.period = str(int(period_value)) + " " + period_suffix

		return self.period

# SIGNAL vector
class SignalVector(Signal):
	def __init__(self):
		Signal.__init__(self)
		self.ascending = False

	def __str__(self):
		if self.ascending == True:
			order = "ascending"
		else:
			order = "descending"

		ret = "name={0:s}, role={1:s}, type={2:s}, pos={3:d}, size={4:d}, order={5:s}"\
			.format(self.name, self.role, self.type, self.pos, self.size, order)

		if self.role != 'out_vec':
			ret += ", value={0:s}".format(self.value)

		return ret

# TEST definition
class Test:
	def __init__(self):
		self.name = ""
		self.clock_reset = ""
		self.clock_disable = ""
		self.rememberState = False
		self.content = []

# TEST: sequence command
class TestSequence:
	def __init__(self):
		self.list = []

# TEST step command
class TestStep:
	def __init__(self):
		self.set_list = {}
		self.expect_list = {}
		self.after = ""

# TEST script command
class TestScript:
	def __init__(self):
		self.file = ""
