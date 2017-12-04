### Modules and Functions
***S9Compressor.py***
1. `encoder(data, length)`
	Using Simple9 algorithm, compress as many number as possible into 28-bit, then record the compress information in the first 4-bit header. The input variable *data* is a list of raw data, and *length* is the length of this list. The output will be a list of compressed data.

2. `decoder(data)`
	Using Simple9 algorithm to decompress a list of data. Reading the first four bits to figure out how many raw numbers are compressed in each number, then use the corresponding method to uncompress. The input variable is a list of compressed data, and the output for this function is a list of decompressed data.

***compress.py***
1. `docidPrepare(docidList)`
	This function is used for prepare the docid for compression. The input data is a list of docid, in ASC order. This function will calculate the difference between each docid and the docid before it. Except the first one, replace all docids with the difference in the list. Then return the new version of docid list.

2. `blockPacker(chunks, chunksInfo)`
	This function is used to pack blocks for a list of chunks. This function will be called once all of the inverted index for a term are processed. Input data are *chunks* and *chunksInfo*. *chunks* may contain one or more chunks, each chunk contains at most 256 integers (128 docids + 128 frequency). *chunksInfo* stores the information for each chunk, which is (chunk size, last docid in this chunk). To implement the chunk-wise compression, during the packing, this function will calculate whether the size of current block will exceed 64KB after adding next chunk into block. If exceed, stop packing process, append this block into the block list, then clear this block for the next packing.
	For each block, the format is: `[metadata, block content]`, the format of metadata is: `[metadata size, lastDocID0, chunk size0, lastDocID1, chunk size1, ...]`. Each block’s format is: `[chunk0, chunk1, chunk2, ...]`.
	This function will return the size of the input *chunks* after it is packed into block(s), and also the list of chunks after packing.

3. `compress(docidList, freqList)`
	This function is used to compress the input *docidList* and *freqList*, return a list of blocks as the result of compression.
	First, this function will get every 128 docids and their frequencies, append these data into a temporary list in format `[docid0, docid1, docid2,...docid127, freq0, freq1, freq2,...,freq127]`. Then prepare the docids by calling function `docidPrepare(docidList)`. Each of the temporary list is a chunk, all chunks will be append to a list of chunks. After all data from *docidList* and *freqList* is processed, this function will call `blockPacker(chunks, chunksInfo)` to help packing these chunks into a list of blocks.
	The return data for this function is the list of packed blocks and it’s size.

4. `writeLexicon()`
	This function is used to write(append) the current data in the buffer into the new Lexicon file. The output format is: `term: head position, tail position, the # of docs which contain this term \n`.
	After writing, buffer will be cleared in this function.

5. `writeNewII()`
	Similar with function `writeLexicon()`, this function helps to write the blocks into inverted index file in binary format, then clear the buffer after writing.

6. `main()`
	In this function, the original inverted index file and lexicon file are opened. For each term in the lexicon file, fetch all inverted index from inverted index file corresponding to this term, and split these data into two lists: *docidList* and *freqList*. Then call function `compress(docidList, freqList)` to compress the data into blocks.
	After getting the compressed blocks and the total size of these blocks, this function will save blocks into inverted index buffer, and save the new lexicon into lexicon buffer.
	After each 10000000 terms are processed, this function will call `writeNewII()` and `writeLexicon()` to write the data into files, then clear the buffer.
	After all the terms in the lexicon file are processed, the loop ends. However, there still might be some data in the buffer waiting to be written into files. So i call the `writeNewII()` and `writeLexicon()` again outside the loop before the end of this function.
