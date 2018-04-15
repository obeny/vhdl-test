import Utils as UT

def process(component):
	content = " {0:s} 0 0 l\n".format(UT.TimeUtils.timeToInterval(component.interval))
	return UT.TimeUtils.timeValueInNsFromTime(component.interval), content
