import sys
import struct
from io import FileIO, BufferedWriter
import S9Compressor as S9

BLOCKSIZE = (64*1024) / 4			# number of Int
LexiPos = 0							# record the current position for new lexicon writing
lexiconBuffer = []
IIBuffer = []
WriteThreshold = 0



def docidPrepare(docidList):		# calculate the diff, return the shorter version list
	res = [docidList[0]]
	for i in xrange(1, len(docidList)):
		res.append(docidList[i] - docidList[i-1])
	return res

def blockPacker(chunks, chunksInfo):
	TotalSize = 0		# total size for this term's inverted index
	blocks = []			# [[metadata, block], [metadata, block], ...]
	metadata = [0]		# [metadata size, [last docid, chunk size], [last docid, chunk size], ...]
	currentTotalSize = 1		# number of Int, initialize 1 because of the metadata size
	block = []
	
	for i in xrange(len(chunksInfo)):
		if (currentTotalSize + 2 + chunksInfo[i][0]) <= BLOCKSIZE:
			currentTotalSize += (2 + chunksInfo[i][0])
			metadata[0] += 1
			metadata.append(chunksInfo[i][::-1])
			block.append(chunks[i])

		else:						# when current block is full
			blocks.append([metadata,block])	# add block to blocks
			TotalSize += currentTotalSize
			metadata = [0]			# initialize
			currentTotalSize = 1
			block = []

			currentTotalSize += (2 + chunksInfo[i][0])
			metadata[0] += 1
			metadata.append(chunksInfo[i][::-1])
			block.append(chunks[i])

	blocks.append([metadata,block])
	TotalSize += currentTotalSize
	
	return TotalSize, blocks



def compress(docidList, freqList):
	docLen = len(docidList)
	chunks = []				# [chunk, chunk, ...]
	chunksInfo = []			# [[chunksize, lastdocId], ...]

	for i in xrange(docLen/128 + 1):
		tmpdocidList = docidList[i*128 : (i+1)*128]
		tmpfreqList = freqList[i*128 : (i+1)*128]
		if len(tmpdocidList) == 0:
			break

		lastdocId = tmpdocidList[-1]
		tmpLen = len(tmpdocidList)
		tmpdocidList = docidPrepare(tmpdocidList)

		tmpList = tmpdocidList + tmpfreqList
		chunk = S9.encoder(tmpList, tmpLen * 2)

		chunks.append(chunk)
		chunksInfo.append([len(chunk), lastdocId])	

	return blockPacker(chunks, chunksInfo)
	
def writeLexicon():
	# outLexFile = open("newLexicon.txt", 'a')
	with BufferedWriter(FileIO("newLexicon.txt", "a")) as outLexFile:
		for item in lexiconBuffer:
			outLexFile.write(item[0] + ':' + str(item[1]) + ',' + str(item[2])+ ',' + str(item[3]))
			outLexFile.write('\n')

	del lexiconBuffer[:]
	outLexFile.close()
	return
	
def writeNewII():
	# newII = open("InvertIndex.txt", 'ab')
	
	
 	with BufferedWriter(FileIO("InvertIndex.txt", "ab")) as newII:
 		def writeByte(Integer):
			return newII.write(struct.pack('I', Integer)[::-1])
		
		for blocks in IIBuffer:
			for block in blocks:
				writeByte(block[0][0])			# write size of metadata header
				for number in [item for sublist in block[0][1:] for item in sublist]:		# flatten the tmpList
					writeByte(number)

				for number in [item for sublist in block[1] for item in sublist]:		# flatten the list
					writeByte(number)
	del IIBuffer[:]
	newII.close()
	return

def main():
	global LexiPos
	global WriteThreshold

	LexFile = open("Lexicon.txt", 'r')
	iiFile = open("origInvertedIndex.txt","rb")

	for line in LexFile:
		docidList = []
		freqList = []

		lexInfo = line.split(":")
		IndexInfo = lexInfo[-1].split(",")
		IndexInfo = [int(item) for item in IndexInfo]		# [head, tail, number of docs]


		iiFile.seek(4*IndexInfo[0],0)


		for i in xrange(IndexInfo[-1]):
			docidList.append(struct.unpack('<I', iiFile.read(4)[::-1])[0])
			freqList.append(struct.unpack('<I', iiFile.read(4)[::-1])[0])

		compressedII = compress(docidList, freqList)			# compress data into blocks

		TotalSize, blocks = compressedII[0], compressedII[1]

		IIBuffer.append(blocks)
		lexiconBuffer.append([lexInfo[0], LexiPos, LexiPos+TotalSize, IndexInfo[-1]])
		LexiPos += TotalSize
		WriteThreshold += TotalSize

		if WriteThreshold > 10000000:
			print "writing..."
			WriteThreshold = 0	# reset WriteThreshold
			writeLexicon()	
			writeNewII()

	writeLexicon()
	writeNewII()
		
	iiFile.close()
	LexFile.close()
	
main()