import urllib
import urllib2
import os
import re
from google import search
from urlparse import urlsplit
from bs4 import BeautifulSoup
from urlparse import urljoin
import numpy
from scipy.sparse import csc_matrix
import robotexclusionrulesparser
import robotparser
import urlparse
import requests
import mimetypes
import socket
import datetime

class Crawl(object):
	def __init__(self):
		self.starttime = datetime.datetime.utcnow()
		self.timeout = 3

		self.statistic = {"404":0, "403":0, "totalSize":0.0}		# statistic data for the output.
		self.urlInfo = {}		# store attributes of each url, used for output. PGID[ 0. crawled time, 1. size , 2.estimate rank, 3.final rank]
		self.urlWL = []			# to store urls, waiting list 
		
		self.vistedList = {}	# check repeat & store all visted links
		self.crawledList = {}	# store url which is alreay crawled
		self.urlID = 0

		self.rankDic = {}		# to store urls(id) and their ranks
		self.blackListType = {'jpg', 'pdf', 'jsp', 'cms', 'asp', 'webm', 'gz', 'sig', 'ogv', 'png', 'zip', 'txt'}

		self.siteCounter = {}	# to limit the pages from per site
		self.siteLimit = float('Inf')		# set the max pages from the same site

		self.PG = {}			# save page's url, and index 
		self.PGreverse = {}		# save page's index, and url for reverse lookup
		self.PGID = 0

		self.mapping = {}		# to store the mapping relation between links (use PGID)
		self.linkLimit_PerPage = 30			# prevent too much links are crawled in a same page.

	def downloadPage(self, url):
		path='/Users/gpz/Desktop/downloadPage/'
		file_name = str(self.vistedList[url]) + '.html'
		dest_dir=os.path.join(path,file_name)  
		urllib.urlretrieve(url , dest_dir)


	def getStartPage(self, query, number):
		result = []
		for item in search(query, tld="co.in", num=number, stop=1, pause=1):
			result.append(item)
		for url in result:							# for the first 10 url
			if url not in self.vistedList:
				self.vistedList[url] = self.urlID		# add to visted list
				self.urlID += 1

				size = self.formatFilter(url)
				if size:								# if HTML
					self.urlWL = [url] + self.urlWL		# enqueue to waiting list
					self.PG[url] = self.PGID			# add to page dictionary for ranking
					self.PGreverse[self.PGID] = url
					self.urlInfo[self.PGID] = [datetime.datetime.utcnow().isoformat(), size]			# add PGID to urlInfo, with crawled time and size
					self.statistic['totalSize'] += float(size)
					self.PGID += 1
		return

	def addMapping(self, Url, toUrl):					# add map relationship to mapping dictionary
		UrlID = self.PG[Url]
		toUrlID = self.PG[toUrl]
		if UrlID not in self.mapping:
			self.mapping[UrlID] = [toUrlID]
		else:
			if toUrlID not in self.mapping[UrlID]:
				self.mapping[UrlID].append(toUrlID)
		return


	def findUrl(self, PageLimit):			# get url from the content of a list of urls
		while self.PGID < PageLimit:
			try:
				url = self.urlWL.pop()
			except IndexError:				# if waiting list is empty
				print "The url waiting list is empty, please modify function 'updateRank' or some parameters and try again ! "
				break

			self.crawledList[url] = 1

			try:							# catch exception when open urls, if error, discard this url
				urlf = urllib2.urlopen(url, timeout = self.timeout)
				soup = BeautifulSoup(urlf.read(), "html.parser")
			except urllib2.HTTPError, err:
				if err.code == 404:
					self.statistic["404"] += 1
					print "404 page not found"
				elif err.code == 403:
					self.statistic["403"] += 1
					print "403 Access denied"
				else:
					print "some error occured:", err.code

				continue
			
			except urllib2.URLError, err:
				print "some other error occured:", err.reason
				continue
			
			except:
				print "some other error occured:"
				continue

								
			link_list = soup.findAll("a", href=True)
			linkCounter = 0
			for link in link_list:
				fullUrl = urljoin(url, link["href"]).rstrip('/')		# Complete relative URLs in the current page
				if fullUrl.split('.')[-1] not in self.blackListType:	# a serial of url filters

					if fullUrl in self.PG and fullUrl != url:					# add mapping relation if found one
						self.addMapping(url, fullUrl)

						# check if already visted, check cgi page, check download page, check login page
					if (fullUrl not in self.vistedList) and ("cgi" not in fullUrl) and ("account" not in fullUrl) and ("login" not in fullUrl) and ("download" not in fullUrl):
						self.vistedList[fullUrl] = self.urlID
						self.urlID += 1
						siteBaseUrl = self.getBaseUrl(fullUrl)
						if (siteBaseUrl not in self.siteCounter) or (self.siteCounter[siteBaseUrl] > self.siteLimit):
							
							print fullUrl							# print while testing

							size = self.formatFilter(fullUrl)		# return 0 if not html OR return the size of this page
							if size != 0:							# if it's html
								try:
									is_allowed = self.getRobotExclu(siteBaseUrl)
								except:
									print "robots.txt is not reachable in this website."
									continue

								if is_allowed == 1:				# if allowed to access	
									if siteBaseUrl not in self.siteCounter:	# count current site in siteCounter
										self.siteCounter[siteBaseUrl] = 1
									else:
										self.siteCounter[siteBaseUrl] += 1

									self.PG[fullUrl] = self.PGID			# add to PG and PGreverse
									self.PGreverse[self.PGID] = fullUrl
									self.urlInfo[self.PGID] = [datetime.datetime.utcnow().isoformat(), size]			# add PGID to urlInfo, with crawled time and size
									self.statistic['totalSize'] += float(size)
									self.PGID += 1

									#self.downloadPage(url)				# if text/html, download the current page
									linkCounter += 1
									self.addMapping(url, fullUrl)			# add mapping relation
									self.urlWL = [fullUrl] + self.urlWL		# add waiting list

									if self.PGID%10 == 0:					# display the progress
										print str(float(self.PGID)/PageLimit)

									if linkCounter > self.linkLimit_PerPage:			# crawl a new page when reach the limit
										break
									

		matrix = self.matrixGenerator()
		Rank = self.pageRank(matrix)
		self.updateRankinfo(Rank)
		self.output()
		return


	def getBaseUrl(self, url):			# get base url, e.g. "http://www.xxxx.xxx"
		parsed = urlsplit(url)
		host = parsed.netloc
		return 'http://' + host


	def formatFilter(self, url):		# check if the url type is text/html
		try:
			signal.signal(signal.SIGALRM, self.handler)
			signal.alarm(5)
			
			response = requests.get(url, timeout = self.timeout)
			content_type = response.headers['content-type']

			signal.alarm(0)
			
			if content_type.split(";")[0] == 'text/html':
				return response.headers["Content-Length"]			# if text/html, return page size
			else:
				return 0
		
		except AssertionError:
			print "get format timeout."
			return 0

		except:
			return 0


	def getRobotExclu(self, url):
		try:
			signal.signal(signal.SIGALRM, self.handler)
			signal.alarm(5)
			BaseUrl = self.getBaseUrl(url)
			AGENT_NAME = '*'
			parser = robotparser.RobotFileParser()
			parser.set_url(urlparse.urljoin(BaseUrl, 'robots.txt'))
			parser.read()
			url = url.encode('utf-8')
			signal.alarm(0)
			return parser.can_fetch(AGENT_NAME, url)
		except AssertionError:
			print "get robots.txt time out"
			return 0


	def matrixGenerator(self):						# export the mapping dictionary to a n*n relation matrix
		matrix = [[0 for col in xrange(self.PGID)] for row in xrange(self.PGID)]
		for i in self.mapping:
			length = len(self.mapping[i])
			for j in self.mapping[i]:
				matrix[i][j] = (1.0/length)
		return matrix

	def updateRankinfo(self, rank):						# update rank dictionary and update url waiting list
		Rank_Sort = []
		for i in xrange(self.PGID):
			self.rankDic[i] = rank[i]
			self.urlInfo[i].append(rank[i])

		return


	def pageRank(self, Matrix):		# read a n*n matrix
		MinSum = 0.001			# the min sum of pageranks between iterations, below this value will be converged
		Prob = 0.85			# probability of following a transition. 1-s probability of teleporting to another state.

		L = len(Matrix)
		A = csc_matrix(Matrix, dtype = numpy.float)			# transform G into markov matrix A
		rowSums = numpy.array(A.sum(1))[:,0]
		ri, ci = A.nonzero()
		A.data /= rowSums[ri]

		sink = rowSums==0							# check sink states
		
		r0 = numpy.zeros(L)							# compute pagerank R until converge
		r1 = numpy.ones(L)

		while numpy.sum(numpy.abs(r1-r0)) > MinSum:
			r0 = r1.copy()
			for i in xrange(L):						# calculate each pagerank at a time
				
				Ai = numpy.array(A[:,i].todense())[:,0]	# number of inlinks
				Bi = sink/float(L)					# sink state
				Ci = numpy.ones(L)/float(L)

				r1[i] = r0.dot(Ai*Prob + Bi*Prob + Ci*(1-Prob))

		return r1/float(sum(r1))


	def output(self):
		print  "start writing........"
		file = open("BFSoutput.csv", "w")
		file.write("ID, URL, Time, Size, final page rank\n")
		for ID in self.urlInfo:
			writeContent = str(ID) + "," + self.PGreverse[ID] + "," + self.urlInfo[ID][0] + "," + self.urlInfo[ID][1] + "," + str(self.urlInfo[ID][2]) + "\n"
			try:
				file.write(writeContent)
			except:
				continue

		file.write("404 numbers:," + str(self.statistic["404"]))
		file.write("\n403 numbers:," + str(self.statistic["403"]))
		file.write("\ntotalsize:," + str(self.statistic["totalSize"]))
		spendTime = datetime.datetime.utcnow()-self.starttime
		file.write("\ntotalTime:," + str(spendTime))

		file.close()


	def handler(self, signum, frame):
		raise AssertionError

# run the code


A = Crawl()
A.getStartPage('ebbets field',10)
A.findUrl(1200)
