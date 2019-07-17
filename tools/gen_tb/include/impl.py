import log
import XmlHandler as XMLH
import VectorWriter as VW

# AppGenTb class - main class
class AppGenTb:
	def __init__(self, xml, out, scripts, target, verbose):
		log.setVerbose(verbose)
		self.xml = xml
		self.out = out
		self.scripts = scripts
		self.target = target

	def run(self):
		TW = __import__(self.target)

		backend = TW.BackendDataHandler()
		xmlHandler = XMLH.XmlHandler(self.xml, backend)
		self.meta = xmlHandler.buildMeta(self.out)

		self.vectorWriter = VW.VectorWriter(self.meta, self.out, self.scripts)
		self.testWriter = TW.TestWriter(self.meta, self.out, self.vectorWriter)

		self.testWriter.run()
		log.info("testbench duration: {0:s}"\
			.format(self.testWriter.getTestbenchDuration()))
		log.info("FINISHED!")
