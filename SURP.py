import glob
import sys,re
import PyPDF2
from collections import Counter
from nltk.stem import * 
import math
import operator
import pickle

def ConsoleOut(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()
    sys.stdout.write('%s\r\r' % (' '*len(msg)))
    sys.stdout.flush()

def getWordCounts(docId,pdf):
    pdfReader = PyPDF2.PdfFileReader(open(pdf, 'rb'))
    wordList = []
    for i in range(pdfReader.getNumPages()):
        msg = "Reading Document: %i of %i at Page %i of %i"%(docId+1,len(docList),i,pdfReader.getNumPages()) 
        ConsoleOut(msg)
        pageObj = pdfReader.getPage(i)
        pageText = pageObj.extractText()
        pageText = re.compile('\w+').findall(pageText.encode('ascii', 'ignore'))        
        wordList += [stemmer.stem(i) for i in pageText]
    return Counter(wordList)

def populateMatrix():
    global wordDict,docList
    for docId in range(len(docList)):
        a = getWordCounts(docId,docList[docId])
        for word in a:
            if word not in wordDict:
                wordDict[word] = {}
            wordDict[word][docId] = 1+math.log10(a[word])

def normalize(w):
    sqrSum = 0
    for a in w:
        sqrSum += w[a]**2
    if sqrSum==0:
        return w
    sqrSum = sqrSum**0.5
    for a in w:
        w[a] /= sqrSum
    return w


def scanFolder():
    populateMatrix()
    dset = {}
    dset['wordDict'] = wordDict
    dset['docList'] = docList
    pickle.dump(dset, open(".pdf-tf.pickle", "wb"))

def LoadData():
    global wordDict,docList
    try:
        dset = pickle.load(open(".pdf-tf.pickle", "rb"))
        if set(dset['docList'])!=set(docList):
            raise ValueError('The list of pdfs in the folder has changed, Rescanning the folder')
        wordDict = dset['wordDict']
    except (OSError, IOError) as e:
        print "No Previous Pdf Scan data found, Rescanning the folder"
        scanFolder()
    except ValueError as e:
        print e.args[0]
        scanFolder()


stemmer = SnowballStemmer("english")#PorterStemmer()
docList = glob.glob('./*.pdf')
wordDict = {}
LoadData()

loop = "a"
while loop!="exit":
    query = raw_input("\nEnter your query :")
    query = re.compile('\w+').findall(query.encode('ascii', 'ignore'))
    q = [stemmer.stem(i) for i in query]

    #term frequecy for query
    tf = Counter(q)

    #inverse document frequency for query
    idf = {}
    for a in tf:
        if a in wordDict:
            idf[a] = len(docList)/len(wordDict[a]) if len(wordDict[a])>0 else 0
        else:
            idf[a] = 0

    #weighing the query terms
    q_wts = {}
    for a in tf:
        q_wts[a] = (1+math.log10(tf[a]))*idf[a]
    q_wts = normalize(q_wts)

    #term frequency for query terms in docs
    doc_cts = {}
    for i in range(len(docList)):
        doc_cts[i] = {}
        for a in tf:
            if not a in wordDict:
                doc_cts[i][a] = 0
            elif i not in wordDict[a]:
                doc_cts[i][a] = 0
            else:
                doc_cts[i][a] = wordDict[a][i]

    #document matching
    doc_wt = {}
    for i in doc_cts:
        doc_wt[docList[i]] = 0
        doc_cts[i] = normalize(doc_cts[i]) #normalize doc tf
        for a in tf:
            doc_wt[docList[i]] += doc_cts[i][a]*q_wts[a] #cosine of query weights and doc tf

    #Print Results in sorted order
    doc_wt = sorted(doc_wt.items(), key=operator.itemgetter(1), reverse=True)
    print "Ranked Matches:\n================" 
    for a in doc_wt:
        if a[1]>0:
            print a[0]
    loop = raw_input("Type exit to quit or press enter to continue \n")