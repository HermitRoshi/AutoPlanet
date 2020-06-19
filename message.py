import xml.etree.ElementTree as ET
from enum import Enum

class Message():

	def __init__(self, streamString):
		self.__type = None
		self.__action = None
		self.__code = None
		self.__rawData = None
		self.__cmd = ''
		self.__parse(streamString)

	def __parse(self, streamString):
		self.__rawData = streamString

		if self.__rawData.startswith('<msg'):
			self.__type = MessageTypeEnum.MSG
			self.__parseMsg(streamString)
		elif self.__rawData.startswith('`xt`'):
			self.__type = MessageTypeEnum.XT
			self.__parseXt(streamString)
		elif self.__rawData.startswith('<cross-domain-policy>'):
			self.__type = MessageTypeEnum.POLICY

	def __parseMsg(self, streamString):
		# This is hacky, I hate it, but it works. I'll change it...TODO
		start = streamString.find('action=\'', 10, 100)
		end = streamString.find('\'', start+9, 100)
		self.__action = streamString[start+8: end]

		self.__cmdFromXml(streamString)

	def __parseXt(self, streamString):
		split_string = streamString.split('`')
		self.__action = split_string[2]
		self.__code = split_string[3]

	def __cmdFromXml(self, data):
		cleanData = data.replace("<![CDATA[<dataObj>","").replace("</dataObj>]]>","")
		root = ET.fromstring(cleanData)

		for node in root.iter("var"):
		    if node.attrib['n'] == "_cmd":
		    	self.__cmd = node.text

	def getValue(self, field):
		cleanData = self.__rawData.replace("<![CDATA[<dataObj>","").replace("</dataObj>]]>","")
		root = ET.fromstring(cleanData)

		for node in root.iter("var"):
		    if node.attrib['n'] == field:
		    	return node.text

	def getUserId(self):
		if self.__action == "userGone":
			root = ET.fromstring(self.__rawData)
			return root.find("body//user").attrib['id']
		else:
			return -1

	def getMessageType(self):
		return self.__type

	def getMessageAction(self):
		return self.__action

	def getMessageCode(self):
		return self.__code

	def getMessageRaw(self):
		return self.__rawData

	def getXmlCmd(self):
		return self.__cmd

class MessageTypeEnum(Enum):
	XT = 0
	MSG = 1
	POLICY = 2