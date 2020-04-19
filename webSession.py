import requests
import pickle
import os

from bs4 import BeautifulSoup

from utils.constants import CONSTANTS

class WebSession:

	def __init__(self, sessionCookie, userAgent):

		# Requests session
		self.__session = requests.Session()

		# Save off session cookie in case we need it
		self.__sessionCookie = sessionCookie

		# This should be done when the headers are built but for some
		# reason it does not seem to accept it. So it is staying here.
		self.__session.headers.update({"User-Agent": userAgent})

		# Logged in flag
		self__loggedIn = False

		# User info dict. Has username, userid, hashpassword.
		self.userInfo = {}

	def login(self, username, password):

		# If we saved cookies from previous session use them
		if os.path.exists("./config/cookies/" + username.lower() + ".cfg"):
			cookie_file = open("./config/cookies/" + username.lower() + ".cfg", "rb")
			self.__session.cookies.update(pickle.load(cookie_file))
		else:
			# No cookies? We need the cloudflare clearance
			cf_clearance = requests.cookies.create_cookie(domain='.pokemon-planet.com',name='cf_clearance',value=self.__sessionCookie)
			self.__session.cookies.set_cookie(cf_clearance)

		params = self.__buildParams(username, password)
		postHeaders = self.__buildPostHeaders(params)

		loginRequest = self.__session.post(CONSTANTS.LOGIN_PAGE_URL,
										   headers=postHeaders,
										   data=params)

		getHeaders = self.__buildGetHeaders()

		if loginRequest.status_code == 200:
			userInfoRequest = self.__session.get(CONSTANTS.USER_PAGE_URL, 
												 headers=getHeaders)
			if userInfoRequest.status_code == 200:
				with open("./config/cookies/" + username.lower() + ".cfg", 'wb') as cookie_file:
				    pickle.dump(self.__session.cookies, cookie_file)
				return self.__parseUserInfo(userInfoRequest.text)

		self.__loggedIn = False
		return False


	def __buildParams(self, username, password):
		"""Build and return parameters.

		Parameters which will be used to post a login request. Includes
		username, password, and a number of hidden fields.
		"""
		# Create a dict with parameters we know so far
		params = {"user": username, "passwrd": password}
		# Get html from main page. Used to get name and value of a 
		# hidden post field.
		mainPageHtml = self.__session.get(CONSTANTS.MAIN_PAGE_URL).text
		# Use beautifulsoup to parse the plain text html
		soup = BeautifulSoup(mainPageHtml, "html.parser")

		# Get all hidden tags. This is kind of risky I think. Especially
		# for long term use of this tool. We are not guaranteed to get 
		# some other hidden input fields.
		hiddenInputs = soup.find_all("input", {"type": "hidden"})

		# Add hidden inputs to params
		for hiddenInput in hiddenInputs:
			params[hiddenInput["name"]] = hiddenInput["value"]

		return params

	def __buildGetHeaders(self):
		"""Builds and returns get headers.

		Headers which will be use to get user info.
		"""

		# Headers dict
		headers =  {"Host": "pokemon-planet.com",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
					"Accept-Language": "en-US,en;q=0.5",
					"Accept-Encoding": "gzip, deflate",
					"Connection": "keep-alive",
					"Upgrade-Insecure-Requests": "1",
					"TE": "Trailers"}

		return headers

	def __buildPostHeaders(self, params):
		"""Builds and returns post headers.

		Headers which will be use to post a login request. Includes the 
		headers captured by Mozilla Firefox browser.
		"""

		# Headers dict
		headers =  {"Host": "pokemon-planet.com",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
					"Accept-Language": "en-US,en;q=0.5",
					"Accept-Encoding": "gzip, deflate",
					"Content-Type": "application/x-www-form-urlencoded",
					"Origin": "http://pokemon-planet.com",
					"DNT": "1",
					"Connection": "keep-alive",
					"Referer": "http://pokemon-planet.com/",
					"Upgrade-Insecure-Requests": "1"}

		return headers


	def __parseUserInfo(self, info):
		"""Takes in a string of user info and splits it into a dict"""

		# Validate that this actually contains user info
		if '&hashpassword' in info:
			# Split the info into its components
			for pair in info.split("&"):
				pair = pair.split("=")
				self.userInfo[pair[0]] = pair[1]
			self.__loggedIn = True
			return True
		else:
			# We failed to validate so we must not have the correct page
			self.__loggedIn = False
			return False

	def getLoginString(self):
		"""Returns a complete login string for the client"""

		if self.__loggedIn:
			return  ('<msg t=\'sys\'>' +
						'<body action=\'login\' r=\'0\'>' +
							'<login z=\'PokemonPlanet\'>' +
								'<nick>' +
									'<![CDATA['+self.getUsername()+']]>' +
								'</nick>'+
								'<pword>' +
									'<![CDATA['+self.getHashPassword()+']]>' +
								'</pword>'+
							'</login>'+ 
						'</body>'+
				    '</msg>\x00')
		else:
			raise Exception('Cannot produce login string. User not logged in.')

	def getUsername(self):
		"""Returns the username parsed from user info page"""

		if self.__loggedIn:
			return self.userInfo['username']
		else:
			raise Exception('User not logged in.')

	def getId(self):
		"""Returns the id parsed from user info page"""

		if self.__loggedIn:
			return self.userInfo['id']
		else:
			raise Exception('User not logged in.')

	def getHashPassword(self):
		"""Returns the hashed password parsed from user info page"""

		if self.__loggedIn:
			return self.userInfo['hashpassword']
		else:
			raise Exception('User not logged in.')
