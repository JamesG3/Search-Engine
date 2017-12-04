### File descriptions
***compress.py***
This file is used to compress the original inverted index structure, using Simple 9 compress algorithm.
***S9Compressor.py***
This file contains Simple 9 class, includes two method, *encoder* and *decoder*. We will use *encoder* for the compress part.
***Lexicon.txt***
This lexicon file is generated from last assignment (inverted index builder), store the head position, tail position and the size of inverted index for each term.
***origInvertedIndex.txt***
This is uncompressed Inverted index structure.
### How to run
You can use any type of python IDE or terminal to run ***compress.py***. But have to make sure ***compress.py***, ***S9Compressor.py***, ***Lexicon.txt*** and ***origInvertedIndex.txt*** are under the same folder.
After the compress process is done, there will be two new files called ***newLexicon.txt*** and ***InvertIndex.txt*** in the same folder.
### Time and Space performance
The S9 compressor works pretty well on inverted index. I use 80 WET files generate a 10GB inverted index file, then put it to the compressor, generate a 2.67GB compressed inverted index file.
I run this script on my laptop, took me about 1.5 hours. It might be faster if running it on HPC or EC2.
### Limitations and how to improve performance
For the compress part, build a filter to ignore those terms which only have 1 postings. If a word only has 1 postings, means that this term is not appropriate for searching. In most cases, this kind of terms might be some meaningless random characters. Although it also could be serial number or model number, but most of serial numbers may not only appear in one page.
Due to this kind of terms took a lot of space in memory and usually won’t be searched, we can ignore them for better performance.