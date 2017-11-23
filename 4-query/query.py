import struct
import math
import time
import S9Compressor as S9
import getSnippet


lexicon = {}				# term: head, tail, # of docs
pagetable = {}				# docid: position for url line

iiLists = []				# [all data for term1], [all data for term2]
termList = []				# term1, term2, ..
lexiconList = []			# [term1's lexicon], [term2's],...

metaDataList = []			# [[t1's block1 meta], [t1's block2 meta]], [[t2's],[t2's]]

iiCache = {}				# store the current decompressed chunk, [[current SUM, cursor], [the decompressed chunk]]

lp = []						# [block#, chunk#, iiPosition], [block#, chunk#, iiPosition]

termDocFreq = {}			# key:[term's index in termList, DocId], value: Freq

# constances for BM25 calculation
N = 0				# total number of docs in the collection
davg = 0.0			# the average length of docs i the collection
k1, b = 1.2, 0.75

def lexPrepare():
	print "loading lexicon..."
	lexFile = open('newLexicon.txt','r')
	for line in lexFile:
		lexInfo = line.split(':')
		lexicon[lexInfo[0]] = [int(item) for item in lexInfo[1].split(',')]

	lexFile.close()
	return


def pagetbPrepare():		# only save the docid and it's position, using seek later. saving memory, fast.
	global N
	global davg
	print "loading pagetable..."
	pageFile = open('pgtable.txt', 'r')

	position = 0
	counter = 0
	for line in pageFile:
		if counter == 0:			# docId
			position += len(line)
			pageId = int(line)
			pagetable[pageId] = position	# save the postion where url starts
			counter += 1
			N += 1

		elif counter == 1:			# url
			position += len(line)
			counter += 1
		else:						# size
			position += len(line)
			size = int(line)
			counter = 0	

			davg += size	
		
	davg = davg/N

	pageFile.close()
	return

def checkValid(queryList):		# check whether the input query is valid, if valid, return the filtered termlist
	cleanTerm = []
	for term in queryList:
		if term == "":
			continue
		if not str.isalnum(term):
			return 0
		else:
			cleanTerm.append(term)
	return list(set(cleanTerm))			# keep one term if repeat

def sort(termList, lexiconList, sortHelper):	# sort(asc) termList and lexiconList base on the size of inverted index
	sortHelper.sort()
	newTermList = []
	newLexiconList = []

	for pair in sortHelper:
		newTermList.append(termList[pair[-1]])
		newLexiconList.append(lexiconList[pair[-1]])
	return newTermList, newLexiconList

def openList(head, tail):			# load the compressed inverted index list into iiLists
	global iiLists
	iiFile = open("InvertIndex.txt",'r')
	iiFile.seek(head*4,0)
	tmpii = []						# might contain several blocks
	counter = tail - head
	for number in iter(lambda: iiFile.read(4)[::-1], ''):
		if counter == 0:
			break
		counter -= 1
		integer_value = struct.unpack('<I', number)[0]
		tmpii.append(integer_value)
	
	iiLists.append(tmpii)
	# print iiLists

	return


def closeList():
	del iiLists[:]
	del termList[:]
	del lexiconList[:]
	del lp[:]
	del metaDataList[:]
	iiCache.clear()
	termDocFreq.clear()
	return

def getMetadata():				# load metadata for all blocks of each term
	for i in xrange(len(termList)):
		L = lexiconList[i][1] - lexiconList[i][0]
		currL = 0				# initialize as 1, for the size of metadata in 1st block
		headers = []

		while currL != L:
			currentHeader = []
			headSize = iiLists[i][currL]
			currL += 1
			currentHeader = iiLists[i][currL : currL+headSize*2]
			headers.append(currentHeader)

			for j in xrange(1, headSize*2,2):
				currL += currentHeader[j]
			
			currL += headSize*2

		metaDataList.append(headers)		# store headers for each term into a global list
		# print metaDataList

	return

# decompress, cache, return num stuff
def getnexGEQ(i, chunksize, iiPosition, did, iscached):
	global iiLists
	chunk = iiLists[i][iiPosition: iiPosition+chunksize]
	
	# print chunk
	# print S9.decoder(chunk)
	
	if iscached == 0:			# if not in the current cache
								# init or replace the cache
		iiCache[i] = [[0, 0],S9.decoder(chunk)]	# [SUM, cursor], chunk

	SUM, cursor = iiCache[i][0][0], iiCache[i][0][1]
	for j in xrange(cursor, len(iiCache[i][1])/2):
		if SUM >= did:
			iiCache[i][0][0], iiCache[i][0][1] = SUM, j
			return SUM
		else:
			SUM += iiCache[i][1][j]
	


def nextGEQ(i, did):		# check the next docid >= did, in inverted index for term i
	global lp

	headers = metaDataList[i]	# get headers for term i
	if len(lp) == i:		# need add a new listpointer, initialize
		iiPosition = 0
		for j in xrange(len(headers)):		# read each block's header in headers
			iiPosition += 1					# for the metadata size
			header = headers[j]
			iiPosition += len(header)		# for header size in current block

			for k in xrange(0, len(header), 2):
				if header[k] >= did:
					lp.append([j, k/2, iiPosition])	# record current position (block#, chunk#, iiPosition)
					return getnexGEQ(i, header[k+1], iiPosition , did, 0)		# return the docid >= did
				else:
					iiPosition += header[k+1]	# add the size of the skipped chunk
		return				# if this term doesn't have larger docid, return None
		

	else:
		currentlp = lp[i]	# read lp, locate the last read information
		iiPosition = currentlp[-1]
		blockPos = currentlp[0]
		chunkPos = currentlp[1]
		if headers[blockPos][chunkPos*2] >= did:	# same chunk in the cache
				# actually chunksize and iiPosition are not used in this situation
			chunksize = headers[blockPos][chunkPos*2+1]
			return getnexGEQ(i, chunksize, iiPosition , did, 1)	# read the cached list directly

		for j in xrange(blockPos, len(headers)):		# not same chunk in the cache
			header = headers[j]
			if j != blockPos:				# add header size for each block
				iiPosition += 1
				iiPosition += len(header)

			for k in xrange((chunkPos+1)*2, len(header),2):		# find from next chunk
				if header[k] >= did:
					lp[i] = [j, k/2, iiPosition]
					return getnexGEQ(i, header[k+1], iiPosition, did, 0)
				else:
					iiPosition += header[k+1]

		return			# if cannot find, return None


def getFreq(i, did):
	return iiCache[i][1][iiCache[i][0][1]-1 + len(iiCache[i][1])/2]


def PgScore(did):				# return (BM25 score, cosine score)
	global termList
	global N
	global davg
	global k1
	global b

	pageFile = open("pgtable.txt", 'r')
	pageFile.seek(pagetable[did], 0)
	pageFile.readline()		# url line
	d = int(pageFile.readline())		# size line
	pageFile.close()

	K = k1 * ((1-b) + b*d/davg)			# calculate K
	
	ftList = []							# get ft for each term
	for L in lexiconList:
		ftList.append(L[-1])

	freqList = []						# get frequency for each term
	for i in xrange(len(termList)):
		freq = getFreq(i, did)
		freqList.append(freq)
		termDocFreq[i, did] = freq

	BM25 = 0.0
	cosine = 0.0
	for j in xrange(len(termList)):
		BM25 += math.log((N - ftList[j] + 0.5) / (ftList[j] + 0.5)) * (k1 + 1)*freqList[j] / (K + freqList[j])
		cosine += (math.log(1 + N/ftList[j]) * (1 + freqList[j])) / math.sqrt(d)
	return BM25, cosine


def getDocRankList():			# and operation
	global metaDataList
	global termList
	docRankList = []			# [BM25, did], [BM25, did]
	termNum = len(termList)

	did = 1			# solve the initialize corner case
	flag = 0			# 0: normal, 1: need to find larger did, 2: no more did, exit
	maxDocID = metaDataList[0][-1][-2]		# get maxDocID for the first term

	while did <= maxDocID:
		did = nextGEQ(0, did)
		if did is None:				# no more pages to be found
			break

		for i in xrange(1, termNum):
			nextdid = nextGEQ(i, did)
			if nextdid is None:		# no more pages to be found
				flag = 2			# exit code
				break
			if nextdid > did:
				flag = 1
				break
	
		if flag == 1:			# if not in intersection, find term0's next did
			did = nextdid
			flag = 0
			continue

		elif flag == 2:
			break

		else:				# found a did contains all terms !!
			pgScore = PgScore(did)
			docRankList.append([pgScore[0], pgScore[1], did])
			did += 1

	docRankList.sort(reverse = True)
	
	return docRankList[:10]		# get top 10


def getUrl(docRankList):
	urlList = []
	pageFile = open("pgtable.txt", 'r')
	for doc in docRankList:
		pageFile.seek(pagetable[doc[-1]], 0)
		urlList.append(pageFile.readline()[:-1])		# url line
	pageFile.close()
	return urlList
	
def main():
	global termList
	global lexiconList
	

	while True:
		query = raw_input('Type words for searching: ')
		flag = 0			# 0: normal, 1: not found query
		
		if query == 'exit()':
			print "Release memory..."
			break


		startTime = round(time.time()*1000)

		queryList = query.split(" ")
		cleanTerm = checkValid(queryList)
		if not cleanTerm:
			print "your input is not valid, try again with only letters or numbers"
		else:
			listIndex = 0
			sortHelper = []

			for term in cleanTerm:
				if term in lexicon:
					termList.append(term)
					lexiconList.append(lexicon[term])
					sortHelper.append([lexicon[term][-1], listIndex])
					listIndex += 1
				else:
					print "at least one word in the query doesn't exist"
					flag = 1		# query doesn't exist
					closeList()
					break

			if flag == 1:		# query doesn't exist
				continue

			sortedList = sort(termList, lexiconList, sortHelper)
			termList, lexiconList = sortedList[0], sortedList[1]

			# print termList
			# print lexiconList
			# print "--------"
			for item in lexiconList:
				openList(item[0],item[1])		# load iilists(head, tail)

			getMetadata()		# for each term, get and load all metadata from all blocks

			docRankList = getDocRankList()
			# print docRankList
			urlList = getUrl(docRankList)
			
			if len(docRankList) != 0:
				endTime1 = round(time.time()*1000)
				print "You use " + str(float((endTime1-startTime))/1000) + " seconds before getSnippet."
				print "Waiting...\n"
				
				snippetDic = getSnippet.getSnippet(urlList, termList)

				print "============RESULT============"
				for i in xrange(len(docRankList)):
					print str(i) + ": " + urlList[i]
					print "BM25: " + str(docRankList[i][0])		# BM25 score
					print "cosine: " + str(docRankList[i][1])	# cosine score
					print snippetDic[urlList[i]]				# snippet part
					for j in xrange(len(termList)):				# term freq part
						print termList[j] + ":" + str(termDocFreq[j,docRankList[i][-1]])
					
					print "------------------------------\n"
			else:
				print "oops, the queried terms cannot be found together in any page."
			
			endTime2 = round(time.time()*1000)
			print "You use " + str(float((endTime2-startTime))/1000) + " seconds."
			
			closeList()					# clear all relevant lists after each query
	closeList()
	print "\nBye."				
	return


lexPrepare()
pagetbPrepare()
main()