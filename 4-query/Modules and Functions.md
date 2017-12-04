### Modules and Functions
***getSnippet.py***
1. `getSnippet(urlList, termList)`
	This function open a thread for each url in the urlList. In each thread, calling function `fetch_url(url)` to get the snippet into snippet dictionary. After all threads end, return the snippet dictionary.
	The snippet dictionary’s key is url, value is the generated snippet.

2. `fetch_url(url)`
	This function will open the input url using method `urllib.urlopen()`, then download the plaintext content from this page. And generate the snippet base on the terms in the termList. After each term is generated, add this term to snippet dictionary.

***query.py***
- **Global variables:**
1. `lexicon` - `term: head, tail, # of docs`
	A dictionary stores the lexicon information for each term.

2. `pagetable` - `docid: position for url line`
	A dictionary stores the docid and the it’s position in the pagetable file.

3. `iiLists` - `[all data for term1], [all data for term2]`
	For each query, store whole compressed inverted index for each term, in the order same as `termList`.

4. `termList` - `term1, term2, .. `
	Store the queried terms in the **ASC order of their original inverted index length** (number of pages contain this term). Prepare for the injunctive traverse.

5. `lexiconList` - `[term1's lexicon], [term2's],... `
	Store the lexicon information for each queried term, in the same order as `termList`.

6. `metaDataList` - `[[t1's block1 meta], [t1's block2 meta]], [[t2's],[t2's]]`
	Store all metadata for all queried terms. `metaDataList[i]` contains headers for all blocks corresponding to term i, the structure is like the example above.

7. `iiCache` - `[[current SUM, cursor], [the decompressed chunk]]`
	This data structure is a dictionary. Store the current decompressed chunk of each term. So that the chunk will not be decompressed once and once again while processing. The `[current SUM, cursor]` record the location and docid during reading.
8. `lp` - `[block#, chunk#, iiPosition], [block#, chunk#, iiPosition]`
	This is the list pointer. Record the current block and chunk  and also the inverted index position for each term while processing several inverted index structures. The iiPosition  is used to verify whether there are more blocks to read for each term.
9. `termDocFreq` - `key:[term's index in termList, DocId], value: Freq`
	This dictionary stores the term’s frequency for each selected page. So the key is the pair of term and docid, the value is frequency.
- **Functions:**
1. `lexPrepare()`
	Load lexicon from file to memory. The data structure which stores the lexicon is called `lexicon`.
2. `pagetbPrepare()`
	Load pagetable from file to memory. However, only load the docid and it’s position in the file to memory, for higher performance. Using `seek()` to get url and frequency for certain *docid* if needed.
3. `checkValid(queryList)`
	The input data is a list of strings. If one of the input strings contains special characters, then return 0. If all strings are valid, return the set of queryList (delete the duplicate terms).
4. `sort(termList, lexiconList, sortHelper) `
	Sort *termList* and *lexiconList* by the ASC order of the number of pages which contain each term.
5. `openList(head, tail)`
	Load the compressed inverted index list into *iiLists*
6. `closeList()`
	Clear the data structures after each query. Prepare for next  query.
7. `getMetadata() `
	Load metadata into global variable *metaDataList* for all blocks of each term.
8. `getnexGEQ(i, chunksize, iiPosition, did, iscached) `
	Get the *docid* equal or larger than *did* for term i. The *iscached* is a bool value. If *iscached* is 0, means a new chunk should be decompressed and loaded into cache. If it is 1, traverse the inverted index directly from *iiCache*.
9. `nextGEQ(i, did) `
	Work with function `getnexGEQ()` together to get the the *docid* equal or larger than *did* for term i. Interactive with the global data structure *lp* to read and store the current block and chunk position. Find next did until traverse all blocks for term i. If cannot find *docid* equal or larger than *did*, return None.

10. `getFreq(i, did) `
	Get frequency for term i in the document *did*. Can get directly from *iiCache*.

11. `PgScore(did) `
	Calculate the BM25 and cosine score for document *did*.

12. `getDocRankList()`
	Use injunctive (and) to traverse all inverted index for each term, find those documents contain all these terms. Calculate scores for the list of *did*, return the top 10 *did* and their scores.

13. `getUrl(docRankList)`
	For each url in the input list, use `seek()` to get urls by reading pagetable file.

14. `main()`
	- Call `lexPrepare()` and `pagetbPrepare()` to load these data structures into memory. It might take a minute.
	- Then start the input interface, get user’s query, split the query with space then pass this *queryList* to function `checkValid(queryList)`. (If the return value is 0, it means there are some special characters in the input. Print the message and back to the input interface.)
	- If the return value is a list of strings, then add each term into *termList*, and lookup the *lexicon*, append the number of docids which contain this word into *lexiconList*.
		(If at least one term doesn’t exist in the *lexicon*, print the message and back to the input interface.)
	- Then pass the *termList*, *lexiconList* and an aux list *sortHelper* into function `sort(termList, lexiconList, sortHelper)`, get the sorted *termList* and *lexiconList*.
	- Load compressed inverted index into *iiLists* for each term by calling function `openList(head, tail)`, extract metadata into *metaDataList* by calling `getMetadata()`.
	- Then call function `getDocRankList()` to get the top 10 *did* and their scores. Get urls for these 10 *did* by calling `getUrl()`.
		(If the return value of `getDocRankList()` is an empty list, which means the queried terms cannot be found together in any page, then print the message and back to the input interface)
	- After we have the information of all these urls, call function `getSnippet(urlList, termList)` to generate snippets for each url.
	- Print out all the result in an appropriate format, call function `closeList()`, back to the input interface.
	- The result contains information below for each URL:
		- URL
		- BM25 score
		- cosine score
		- Time spend before getSnippet
		- Snippet
		- Frequency for each term in this URL.
		- Total time for the query.