import thread
import urllib
from bs4 import*
import threading
import urllib2

def getSnippet(urlList, termList):
	snippetDic = {}			# key: url, value: snippetString
	for url in urlList:
		snippetDic[url] = ""
	
	def fetch_url(url,):
	    try:
			html = urllib.urlopen(url).read()
			soup = BeautifulSoup(html,"html.parser")
			text = soup.get_text()
			
			for term in termList:
				try:
					i = text.index(term)
					snippetDic[url] += text[i-15:i+15].replace("\n", "") + "..."
				except:
					pass
	    except:
	    	pass
	    

	threads = [threading.Thread(target=fetch_url, args=(url,)) for url in urlList]
	for thread in threads:
	    thread.start()
	for thread in threads:
	    thread.join()
	
	return snippetDic
