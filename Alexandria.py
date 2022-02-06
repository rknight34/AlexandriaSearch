"""Contains 'Document' and 'DocumentCollection' classes for Alexandria core search functions"""

import json
import re
import pdfplumber
import os
import pickle
import numpy as np
import math
from log import addLog
from wordcloud import WordCloud
from PIL import Image

#from Util import *

class Alexandria:
    """Container class for DocumentCollection to hold nlp model outside of library and handle external functionality"""
    def __init__(self, nlp):
        #umbrella nlp model for text processing across package
        self.nlp = nlp
        self.library = None

    def processDocs(self, path):
        """Converts all files with '.txt' or '.pdf' extension in 'TestDocs' folder to JSON formatted Bag of Word dictionaries in 'Processed' folder (_BoW files)"""
        with os.scandir(path) as items:
            for item in items:

                # open .txt file and read, clean and correct text then create Bag of Words (Dictionary)
                if item.name[-4:] == ".txt":
                    print("F* you, I'm not handling .txt files now")

                    # print("Processing: ", item.name, "....")
                    # myfile = open(r"TestDocs/" + item.name, encoding='utf-8')
                    # txt = myfile.read()
                    # doc = nlp(cleanText(txt))
                    # NLPBoW = NLPcreateBagOfWords(doc)
                    # NLPBoN = NLPcreateBagOfNumbers(doc)

                    # save BoW as a _BoW file in JSON format
                    # saveFile = open(r"Processed/" + item.name[0:-4] + "_BoW.json", "w")
                    # json.dump((NLPBoW,NLPBoN), saveFile)

                    # myfile.close()
                    # saveFile.close()

                # open .pdf file and read, clean and correct text then create Bag of Words (Dictionary)
                elif item.name[-4:] == ".pdf":
                    print("Processing: ", item.name, "....")

                    txtList = self.extractTextPDF(path + "/" + item.name)
                    BoWList = []

                    for page in txtList:
                        doc = self.nlp(self.cleanText(page))
                        NLPBoW = self.NLPcreateBagOfWords(doc)

                        # add each page (BoW, BoN tuple) to List for saving to file later
                        BoWList.append(NLPBoW)

                    # save BoWList as a _BoW file in JSON format
                    saveFile = open(r"Processed/" + item.name[0:-4] + "_BoW.json", "w")
                    json.dump(BoWList, saveFile)
                    saveFile.close()

                else:
                    print("In function 'processDocs' -", item.name, "not a .txt or .pdf")

        print("Processing Complete")

    def extractTextPDF(self, pdf_path):
        """takes pdf_path (from root) and returns list of (pdf) page by page raw text"""
        pagesOfText = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                pagesOfText.append(page.extract_text())

        return pagesOfText

    def cleanText(self, text):

        # remove single quotes (commented out for now as leads to "didn't" becoming "didnt" which confuses spacy/nlp)
        # text = re.sub('\'', '', text)

        # remove unwanted lines starting from special charcters
        text = re.sub(r'\n: \'\'.*', '', text)
        text = re.sub(r'\n!.*', '', text)
        text = re.sub(r'^:\'\'.*', '', text)

        # remove non-breaking new line characters
        text = re.sub(r'\n', ' ', text)

        # remove digits and words containing digits (commented out as I want to process digits)
        # text = re.sub('\w*\d\w*', '', text)

        # remove punctuations (commented out as it causes confusion with "didn't" for example)
        # text = re.sub(r'[^\w\s]', ' ', text)

        # remove commas - they provide no added benefit and confuse processing of large numbers
        text = re.sub(",", "", text)

        # remove brackets as they cause confusion with NLP processor - might have to consider this is future for acronym handling
        text = re.sub(r"[\([{})\]]", " ", text)

        # replace extra spaces with single space
        text = re.sub(' +', ' ', text)

        # lowercase - removed from here as wish to preserve original text for Acronym handling later
        # text = text.lower()

        return text

    def NLPcreateBagOfWords(self, doc):
        """returns dictionary of lemmatised bag of words 'word : frequency' pairs having removed stop words, numbers and tokens length 2 or below"""
        BOWDict = {}

        for token in doc:

            # discard token if a 'STOP WORD' or length less than 3 characters as not deemed important for searching
            if (not token.is_stop
                    and len(token.text) > 2):

                # does the token contain both digits and letters?
                if ('d' in token.shape_
                        and ('X' in token.shape_ or 'x' in token.shape_)):

                    # split token into list of letter only and digit only 'words'
                    listWords = self.handleAlphaNumericToken(token)

                    # add to dictionary for return (increment if existing or create new if not
                    for word in listWords:
                        if word in BOWDict:
                            BOWDict[word] += 1
                        else:
                            BOWDict[word] = 1
                else:

                    # lower case and lemmatise
                    word = (token.lemma_).lower()

                    if word in BOWDict:
                        BOWDict[word] += 1
                    else:
                        BOWDict[word] = 1

        return BOWDict

    def handleAlphaNumericToken(self, token):
        """token = spacy token confirmed as alphanumeric, returns list of separated numbers and words (char only)"""

        # create lower case string
        text = token.lower_

        # split string into list of characters
        textList = list(text)

        # set isCurrentNum flag based on first character
        if textList[0].isdigit():
            isCurrentNum = True
        else:
            isCurrentNum = False

        # cycle through characters and add space on transisiton from numeric to char (or vice versa)
        for i in range(1, len(textList)):
            if textList[i].isdigit() or textList[i] == ".":
                if not isCurrentNum:
                    textList[i] = " " + textList[i]
                    isCurrentNum = True
            else:
                if isCurrentNum:
                    textList[i] = " " + textList[i]
                    isCurrentNum = False

        # turn list into string
        text = "".join(textList)

        # tokenise string and create list of strings (lemmatised)
        doc = self.nlp(text)
        listWords = []

        for token in doc:
            # lower case and lemmatise
            word = (token.lemma_).lower()
            listWords.append(word)

        return listWords

    def loadLibraryFromPickle(self,path):
        """loads self.library (a DocumentCollection object) from pickle file at path. Returns True if successful, False if not"""
        try:
            file = open(path, 'rb')
            self.library = pickle.load(file)
            file.close()
            return True
        except:
            return False

    def saveLibraryToPickle(self, path):
        if self.library is not None:
            self.library.pickleToFile(path)
        else:
            print ("No library to save to file (in 'Alexandria.saveLibraryToPickle')")

    def createLibrary(self):

        docList = []
        with os.scandir("Processed") as items:
            for item in items:
                f = open(r"Processed/" + item.name, "r")
                data = json.load(f)
                f.close()

                doc = Document(item.name[:-9], data[0])
                for page in data[1:]:
                    doc.addPage(page)

                docList.append(doc)

            self.library = DocumentCollection(docList)

    def processInput(self, text):
        """take raw text (text) and process to output list of lemmatised and lower case words"""
        addLog("Search Conducted", text)
        searchWords = []
        NLPtext = self.nlp(text)

        for token in NLPtext:
            if (not token.is_stop
                    and len(token.text) > 2):

                # does the token contain both digits and letters?
                if ('d' in token.shape_
                        and ('X' in token.shape_ or 'x' in token.shape_)):

                    # split token into list of letter only and digit only 'words'
                    listWords = self.handleAlphaNumericToken(token)

                    searchWords += listWords

                else:

                    # lower case and lemmatise
                    word = token.lemma_.lower()

                    searchWords.append(word)

        return searchWords

class Document:
    """myArray - rows are unique words, columns are 'documents'"""
    def __init__(self, docName, initialBoWDict):

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

    def returnTextStringOfUniqueWordsFrequency(self) -> str:
        """combines all unique words : frequency into a string (including multiple entries of same word.
        For use by word cloud"""
        text = ""
        dict = self.getWordFreqTotalPairs()
        for word in dict:

            text = text + ' '.join([word] * int(dict[word])) + ' '

        return text

    def returnWordcloud(self):
        """checks for jpg in 'Processed' folder. Creates wordcloud if not existant
        Returns Pillow Image"""

        filepath = r"Processed/" + self.myName + ".jpg"
        if os.path.exists(filepath):
            return Image.open(filepath)

        else:
            wordcloud = WordCloud(width=3000, height=2000, random_state=1,
                              collocations=False, colormap="Blues").generate(
                self.returnTextStringOfUniqueWordsFrequency())

            wordcloud.to_file(filepath)
            return Image.open(filepath)

class DocumentCollection:
    """container for multiple 'Document' objects and wrap around functionality"""
    def __init__(self, docList):
        """pass list of Document objects to initialise - will accept a list of one"""
        self.myDocs = [docList[0]]
        #used to provide each unique word an index
        self.masterDict = {}

        #requests dict from doc in form {uniqueWord1 : total freq, uniqueWord2 : total freq...}
        tempDict = docList[0].getWordFreqTotalPairs()
        tempFreqList = []

        for word in tempDict:
            self.masterDict[word] = len(self.masterDict)
            tempFreqList.append(tempDict[word])

        self.myArray = np.array([tempFreqList],dtype=np.float_).T

        for doc in docList[1:]:
            self.addDoc(doc, updateTFID=False)

        # make sure the TFID Array is initialised for first doc entry
        self.updateTFIDArray()

    def addDoc(self, doc, updateTFID = True):
        """pass 'Document' object"""
        self.myDocs.append(doc)

        # requests dict from doc in form {uniqueWord1 : total freq, uniqueWord2 : total freq...}
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
        if updateTFID:
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

    def pickleToFile(self, path):

        libraryFile = open(path, 'wb')
        pickle.dump(self, libraryFile)
        libraryFile.close()