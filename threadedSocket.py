import socket # Python socket
import socks  # Socket with proxy
import time

from queue import Queue, Empty
from threading import Thread

from PySide2.QtCore import QObject, Signal, QThread

class ThreadedSocket(QThread):
	receiveSignal = Signal(object)
	timeoutSignal = Signal()
	def __init__(self, ip, port, proxy):
		super(ThreadedSocket, self).__init__()
		self.__ip = ip
		self.__port = port
		self.__proxy = proxy
		self.__send_queue = Queue()
		self.__connected = False
		self.__shutdownCount = 0
		
	def connectSocket(self):
		# If we're currently connected shut down the socket
		if self.__connected:
			self.shutdown()

		# Re-create the socket and connect it
		self.__socket = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
		if self.__proxy[0] == "Enabled":
			if self.__proxy[1] == "http":
				self.__socket.set_proxy(socks.HTTP, self.__proxy[2], int(self.__proxy[3]))
			elif self.__proxy[1] == "socks4":
				self.__socket.set_proxy(socks.SOCKS5, self.__proxy[2], int(self.__proxy[3]))
			elif self.__proxy[1] == "socks5":
				self.__socket.set_proxy(socks.SOCKS4, self.__proxy[2], int(self.__proxy[3]))

		self.__socket.connect((self.__ip, self.__port))
		self.__socket.settimeout(10)

		# Update connected state
		self.__connected = True

		self.__recv_thread = Thread(target=self.__receive, name="Receive Thread")
		self.__recv_thread.setDaemon(True)
		self.__send_thread = Thread(target=self.__send, name="Send Thread")
		self.__send_thread.setDaemon(True)

		# Begin send and receive threads
		self.__recv_thread.start()
		self.__send_thread.start()

	def shutdown(self):
		# Check that we're connected first
		if self.__connected:
			self.__connected = False
			self.__socket.shutdown(socket.SHUT_RDWR)
			self.__send_queue = Queue()

			self.__shutdownCount = self.__shutdownCount + 1
			return True

		# Shutdown failed because we are not connected
		return False

	def getShutdownCount(self):
		return self.__shutdownCount

	def close(self):
		try:
			self.shutdown()
			self.__socket.close()
		except:
			return False
		
		return True

	def sendData(self, dataString):
		"""Adds data to send queue.

		Data is expected in a string and is encoded when added to queue.
		"""

		# Validate that there is data
		if dataString is not None:
			# Add data to queue
			self.__send_queue.put(dataString.encode())

	def __receive(self):
		terminatedMessage = ''
		while self.__connected:
			try:
				data = self.__socket.recv(4096)

				if len(data) > 0:
					decoded_data = data.decode("utf-8", "ignore") 

					# Add data to the current stream
					terminatedMessage = terminatedMessage + decoded_data

					# This segment is last in the current stream
					if decoded_data.endswith('\x00'):

						terminatedMessage = terminatedMessage.split('\x00')

						for piece in terminatedMessage[:-1]:
							self.receiveSignal.emit(piece)

						# Reset the current data stream
						terminatedMessage = ''
			except (socket.timeout, ConnectionAbortedError, ConnectionResetError) as ex:
				self.timeoutSignal.emit()
				return
			except Exception as ex:
				return
		return


	def __send(self):
		while self.__connected:
			try:
				# Get next data in queue, block until there is data
				data = self.__send_queue.get(block=True, timeout=20)

				# Use send all to ensure whole message goes through
				self.__socket.sendall(data)
			except Empty:
				continue
			except:
				# Send failed, something is wrong, for now we just close
				self.close()
		return


