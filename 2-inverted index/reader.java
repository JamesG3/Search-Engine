import java.io.*;
import java.util.*;
import org.archive.io.warc.WARCReaderFactory;
import org.archive.io.ArchiveReader;
import org.archive.io.ArchiveRecord;
import org.apache.commons.io.IOUtils;

public class reader {
    public static Hashtable<Integer, String[]> pageTable = new Hashtable<Integer, String[]>();
    public static Integer exportPgTableFrom = 0;			// index mark for pagetable exporting, pagetable will be exported to file once it reach to a certain size  
    public static Integer bufferSize = 1024;				// inputbuffer and outputbuffer size setting

    // invertList hashtable 
    public static Hashtable<String,ArrayList<Integer>> invertList = new Hashtable<String, ArrayList<Integer>>();   // term: [DocID1, freq1,DocID2, freq2......]

    public static int pageID = 0;

    public static int iiFileNo = 0;    					// ascend value for filename 
    
    public static void main(String[] args) {
    		File[] files = new File("data/wetFiles").listFiles();					// open the path where WET.gz file store
    		for(File file: files) {												
    			String tmpfileName = file.getName();
    			Reader("data/wetFiles/" + tmpfileName);							// get filename for each file, and use function Reader to parse file and build intermediate posting files 
    			System.out.println(pageID);								// use for testing, can be omitted
    		}

        pageTableWriter("data/pgtable.txt");                                           // write the last part of pagetable
        String tmpfileName = "data/wet.paths" + Integer.toString(iiFileNo) + ".txt";	// create a new filename for exporting
        invertListwriter(tmpfileName);								// write the last part of inverted index intermediate posting
        	System.out.println(pageID);									// use for testing, can be omitted
        return;
    }

    public static void Reader(String fileName){
        try{
        	String fn = fileName;
        FileInputStream is = new FileInputStream(fn);
        ArchiveReader ar = WARCReaderFactory.get(fn, is, true);
        for(ArchiveRecord r : ar) {

            if(pageTable.size()!=0 && pageTable.size()>100000) {				// write pagetable once it reach size 100,000, and clear it.
            		pageTableWriter("data/pgtable.txt");
            	}

            if(invertList.size()!=0 && invertList.size()>1000000){			// write invertlist once it reach size 1,000,000, and clear it.
                String tmpfileName = "data/iiPart" + Integer.toString(iiFileNo) + ".txt";
                System.out.println(invertList.size()/1000000);
                invertListwriter(tmpfileName);
                iiFileNo+=1;
            }

            byte[] rawData = IOUtils.toByteArray(r, r.available());
            String content = new String(rawData);

            int termCounter = 0;							// count number of terms for each page

            String tmpword = "";							// save each term during parsing

            for(int j=-1; ++j<content.length();) {          // read all words in the content char by char

                Character cha = content.charAt(j);
                if (Character.isLetterOrDigit(cha)) {			// get word
                    tmpword += cha;
                } else {
                    if(tmpword.length()==0 || !tmpword.matches("^[A-Za-z0-9]+$")){		// if not ascii word, jump to next loop cycle
                    		tmpword = "";
                        continue;
                    }
                    						// if ascii word
                    termCounter += 1;
                    											// check if invertList contains this word
                    boolean iiExists = invertList.containsKey(tmpword);

                    if (!iiExists) {
                        List<Integer> tmpList = Arrays.asList(pageID, 1);			// if not exist, put a initialized <key value> pair into hashtable
                        invertList.put(tmpword, new ArrayList<Integer>(tmpList));
                    }

                    else{										// if exist
                        ArrayList<Integer> tmpArray;
                        tmpArray = invertList.get(tmpword);
                        Integer lastPageId = tmpArray.get(tmpArray.size()-2);
                        
                        if(lastPageId == pageID){					// check whether the last docID is the current page
                            tmpArray.set(tmpArray.size()-1, tmpArray.get(tmpArray.size()-1) + 1);		// if same, modify the frequency
                        }

                        else{									// if not same, append a new record into the value list
                            tmpArray.add(pageID);
                            tmpArray.add(1);
                            }
                        invertList.put(tmpword, tmpArray);		// save the changes into invertList
                    }
                    
                    tmpword = "";       // reset the tmpword
                }
            }

            if(r.getHeader().getUrl() != null) {
                String[] pgitem = {r.getHeader().getUrl(), Integer.toString(termCounter)};

                pageTable.put(pageID, pgitem);			// save the pageID, url, and number of terms into pagetable
                pageID += 1;

            }
        }
        System.out.println("SIZE");						// for testing, can be omitted
        System.out.println(invertList.size());

        is.close();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    
    
    public static void invertListwriter(String fileName) {					// ascii format writer
        try {
            File writename = new File(fileName);
            writename.createNewFile();
            OutputStreamWriter write = new OutputStreamWriter(new FileOutputStream(writename),"ASCII");
            BufferedWriter out = new BufferedWriter(write, bufferSize);
            
            for(String key: invertList.keySet()){								// write each record in the invertList into a new file
            		out.write(key);							// in a format -   term1:pageid1,freq1,pageid2,freq2....,  \n term2.....  
            		out.write(":");
            		ArrayList<Integer> tmpArray;
            		tmpArray = invertList.get(key);

            		for (int j = 0; j < tmpArray.size(); j++) {
            			out.write(Integer.toString(tmpArray.get(j)));
            			out.write(",");
            			}
            		out.write("\n");
            }
            
            out.flush();
            out.close();
            write.close();
            invertList.clear();				//clear the hashtable, release memory

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void pageTableWriter(String fileName) {				// write pageTable in ascii format, append to the same file
        try {
            File writename = new File(fileName);
            writename.createNewFile();
            OutputStreamWriter write = new OutputStreamWriter(new FileOutputStream(writename, true),"ASCII");
            BufferedWriter out = new BufferedWriter(write, bufferSize);

            for(Integer key=exportPgTableFrom; key<pageID ;key++){	// format -  pageid\n url\n numberOfTerms /n
                out.write(Integer.toString(key));
                out.write("\n");
                String[] tmpList;
                tmpList = pageTable.get(key);
                out.write(tmpList[0]);
                out.write("\n");
                out.write(tmpList[1]);

                out.write("\n");
            }

            out.flush();
            out.close();
            write.close();
            exportPgTableFrom = pageID;					// update the start pageID, clear the hashtable, release memory
            pageTable.clear();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }     
}
