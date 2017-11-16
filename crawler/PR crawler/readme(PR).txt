File:
- PRcrawler.py
- PRTop10.py

How to run:
- install all modules used in the program.
- Using terminal: run python PRcrawler.py
- Or use other tools like sublime, etc. copy all code and run.
- Change the query you want to search and page limit No. in the last two lines of the code.


About the parameters:
- there are several parameters can be changed for a certain puropose crawling (e.g. for wider crawling, for deeper crawling, for faster crawling, etc.)

- All parameters have their default value, the program can be run without modify anything, below is the description if you want to change one or several of them:
	
* getStartPage(query, topN)
	Line 320
	This is where to change the string that need to be queried and how many start pages need to have.

* findUrl(pageLimit)
	Line 321
	This is the function which starts the crawling work after get the top N start pages.

* self.timeout = 4
	Line 22
	This is where the timeout setting located. In line 103 and 194, a timeout (seconds) should be set in case of no response or slow response. If there isn't enough page after crawling, probably because the timeout is too short. Some pages have lower response than others but still may contain important informantions(links).

* self.siteLimit = float('Inf')
	Line 37
	This is the limit of page number from each same site. For now, there is no limit. However, if the query string is something popular and wellknown, for example "Trump", there would be so many website about this query. In this kind of situation, a limit should be set by changing float('Inf') to a Integer like 20 or 50.
	In some cases, if the query string is not that popular, the siteLimit should be set to unlimited, or there could be no pages to crawl before reaching 1000.

* self.recalculate = 30
	Line 38
	Recalculate the page rank after a certain number of pages are crawled.
	This parameter should not be too large nor too small, if too large, the most pages being crawled may be lower rank pages. If too small, the recalculation happens so frequently, that waste a lot of time.



* for pair in Rank_Sort:
	Line 253
* for pair in Rank_Sort[-20:]:
	Line 254

One line should be chosen in the program, the other line shold be commented.
Line 253 means every url in the rank would be added to the waiting list.
Line 254 means only top N urls would be added to the waiting list.
Choose 234 if there isn't much url to reach 1000
Or choose 235 if there are too may urls.







