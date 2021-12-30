"""Contains 'Document' and 'DocumentCollection' classes for Alexandria core search functions"""

import numpy as np
import math
from log import addLog


class Document:
    """myArray - rows are unique words, columns are 'documents'"""
    def __init__(self,docName, initialBoWDict):

        self.numPages = 1
        #doc name (could be used for path)
        self.myName = docName
        #this is for indexing each unique word {Word1 : 0, Word2 : 1, Word3 : 2...}
        self.myWordsDict = {}
        #totals of each row - for calculating overall frequency in document
        self.myWordFreq = []

        tempFreqList = []
        for word in initialBoWDict:
            self.myWordsDict[word] = len(self.myWordsDict)
            tempFreqList.append(initialBoWDict[word])

        self.myArray = np.array([tempFreqList],dtype=np.float_).T
        self.myWordFreq = tempFreqList

        # make sure the TFID Array is initialised for first doc entry
        self.updateTFIDArray()

    def __str__(self):
        return self.myName

    def addPage(self,BoWDict):
        self.numPages += 1
        tempList = []
        for i in range(len(self.myWordsDict)):
            tempList.append([0])
        self.myArray = np.append(self.myArray, tempList, axis=1)
        for word in BoWDict:
            if word in self.myWordsDict:
                self.myArray[self.myWordsDict[word],self.numPages-1] = BoWDict[word]
            else:
                #add additional row at bottom for new word with updated element at far right
                tempList2 = []
                for i in range(self.numPages-1):
                    tempList2.append(0)
                #add the new word's frequency for the new doc
                tempList2.append(BoWDict[word])
                self.myArray = np.append(self.myArray, [tempList2], axis=0)

                #update self.myWordsDict to include new word (with indexing)
                self.myWordsDict[word] = len(self.myWordsDict)
        self.myWordFreq = np.sum(self.myArray, axis=1)

        #make sure the TFID Array is updated for new doc
        self.updateTFIDArray()

    def getWordFreqTotalPairs(self):
        """returns a dictionary of all unique words in document with frequency of occurrence in form {word: freq}"""
        dict = {}
        for word in self.myWordsDict:
            dict[word] = self.myWordFreq[self.myWordsDict[word]]

        return dict

    def updateTFIDArray(self):
        # adjusted raw freq array used for conducting searches by page in this case
        self.TFIDFArray = self.myArray.copy()

        columnSum = np.sum(self.TFIDFArray,axis = 0)

        #I've removed the scaling for number of words/tokens on the page as it tends to bias towards pages with few words on them
        #for x in range(len(columnSum)):
            #self.TFIDFArray[:,x] /= columnSum[x]

        rows = (np.count_nonzero(self.TFIDFArray, axis = 1))

        for x in range(len(rows)):
            self.TFIDFArray[x,:] *= math.log(len(columnSum)/rows[x])

    def search(self,listWords):
        """listWords must be pre-processed by NLP to lemmatised words list """
        addLog("Search conducted within Document", str(listWords))

        row = np.zeros((self.numPages,))
        for word in listWords:

            if word in self.myWordsDict:
                row += self.TFIDFArray[self.myWordsDict[word]]
            else:
                addLog("Search Word not found in document", word)

        sortedRow = []

        for i,v in enumerate(row):
            sortedRow.append((i,v))

        sortedRow = sorted(sortedRow, key=lambda i: i[1])

        return sortedRow


class DocumentCollection:
    """container for multiple 'Document' objects and wrap around functionality"""
    def __init__(self,initialDoc):
        self.myDocs = [initialDoc]
        #used to provide each unique word an index
        self.masterDict = {}

        #reqeusts dict from doc in form {uniqueWord1 : total freq, uniqueWord2 : total freq...}
        tempDict = initialDoc.getWordFreqTotalPairs()
        tempFreqList = []

        for word in tempDict:
            self.masterDict[word] = len(self.masterDict)
            tempFreqList.append(tempDict[word])

        self.myArray = np.array([tempFreqList],dtype=np.float_).T

        # make sure the TFID Array is initialised for first doc entry
        self.updateTFIDArray()

    def addDoc(self,doc):
        self.myDocs.append(doc)

        # reqeusts dict from doc in form {uniqueWord1 : total freq, uniqueWord2 : total freq...}
        tempDict = doc.getWordFreqTotalPairs()
        tempList = []
        for i in range(len(self.masterDict)):
            tempList.append([0])
        self.myArray = np.append(self.myArray, tempList, axis=1)
        for word in tempDict:
            if word in self.masterDict:
                self.myArray[self.masterDict[word],len(self.myDocs)-1] = tempDict[word]
            else:
                #add additional row at bottom for new word with updated element at far right
                tempList2 = []
                for i in range(len(self.myDocs)-1):
                    tempList2.append(0)
                #add the new word's frequency for the new doc
                tempList2.append(tempDict[word])
                self.myArray = np.append(self.myArray, [tempList2], axis=0)

                #update self.myWordsDict to include new word (with indexing)
                self.masterDict[word] = len(self.masterDict)

        #make sure the TFID Array is updated for new doc
        self.updateTFIDArray()

    def updateTFIDArray(self):
        # adjusted raw freq array used for conducting searches
        self.TFIDFArray = self.myArray.copy()

        columnSum = np.sum(self.TFIDFArray,axis = 0)

        for x in range(len(columnSum)):
            self.TFIDFArray[:,x] /= columnSum[x]

        rows = (np.count_nonzero(self.TFIDFArray, axis = 1))

        for x in range(len(rows)):
            self.TFIDFArray[x,:] *= math.log(len(columnSum)/rows[x])

    def search(self,listWords):
        """returns sorted list (highest match first) of tuples (docID, search match score)"""
        addLog("Search conducted", str(listWords))

        row = np.zeros((len(self.myDocs),))
        for word in listWords:

            if word in self.masterDict:
                row += self.TFIDFArray[self.masterDict[word]]
            else:
                addLog("Search Word not found", word)

        sortedRow = []

        for i,v in enumerate(row):
            #sortedRow.append((self.myDocs[i],v))
            sortedRow.append((i,v))

        sortedRow = sorted(sortedRow, key=lambda i: i[1], reverse=True)

        return sortedRow

    def returnDocVector(self, docID):
        """returns documents vector as set against 'masterDict;.
        docID is for identifying from this objects 'myDocs' list"""

        array = self.myArray[:, docID]
        array = array / np.sum(array)

        return array

    def docCosineSim(self, docID1, docID2):
        """returns the cosine similarity between the two documents passed (ID for doc in 'myDocs'"""

        array1 = self.myArray[:, docID1]
        array2 = self.myArray[:, docID2]

        cosine_sim = np.dot(array1, array2) / (np.linalg.norm(array1) * np.linalg.norm(array2))

        return cosine_sim

    def getSimilarList(self,docID):
        """returns a list of docIDs (position in myDocs) from closest similarity to least"""

        myList = []

        #run through each document in library and calculate cosine similarity with passed docID
        for i in range(len(self.myDocs)):
            myList.append((i, self.docCosineSim(docID, i)))

        #delete the passed docID as it is clearly 100% similar to itself
        del myList[docID]

        #sort list so most similar appears first
        myList.sort(key=lambda i: i[1], reverse=True)

        return myList