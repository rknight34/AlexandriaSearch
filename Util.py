#external modules
import pdfplumber
import re
import os
import json
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt


#my modules
from log import addLog
from Alexandria import Document, DocumentCollection


def extractTextPDF(pdf_path):
    """takes pdf_path (from root) and returns list of (pdf) page by page raw text"""
    pagesOfText = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pagesOfText.append(page.extract_text())


    return pagesOfText

def cleanText(text):

    #remove single quotes (commented out for now as leads to "didn't" becoming "didnt" which confuses spacy/nlp)
    #text = re.sub('\'', '', text)

    # remove unwanted lines starting from special charcters
    text = re.sub(r'\n: \'\'.*', '', text)
    text = re.sub(r'\n!.*', '', text)
    text = re.sub(r'^:\'\'.*', '', text)

    # remove non-breaking new line characters
    text = re.sub(r'\n', ' ', text)

    # remove digits and words containing digits (commented out as I want to process digits)
    #text = re.sub('\w*\d\w*', '', text)

    # remove punctuations (commented out as it causes confusion with "didn't" for example)
    #text = re.sub(r'[^\w\s]', ' ', text)

    # remove brackets as they cause confusion with NLP processor - might have to consider this is future for acronym handling
    text = re.sub(r"[\([{})\]]", " ", text)

    # replace extra spaces with single space
    text = re.sub(' +', ' ', text)

    #lowercase - removed from here as wish to preserve original text for Acronym handling later
    #text = text.lower()

    return text

def NLPcreateBagOfWords(doc):
    """returns dictionary of lemmatised bag of words 'word : frequency' pairs having removed stop words, numbers and tokens length 2 or below"""
    BOWDict = {}

    for token in doc:

        if (not token.is_stop and len(token.text) > 2 and not token.is_digit):

            word = token.lemma_.lower()
            #word = word.lower()

            if word in BOWDict:
                BOWDict[word] += 1
            else:
                BOWDict[word] = 1

    return BOWDict

def NLPcreateBagOfNumbers(doc):
    """returns dictionary of lemmatised bag of words 'word : frequency' pairs having removed stop words, numbers and tokens length 2 or below"""
    BOWDict = {}

    for token in doc:
        if (token.is_digit):
            if token.text in BOWDict:
                BOWDict[token.text] += 1
            else:
                BOWDict[token.text] = 1

    return BOWDict

def processDocs(nlp):
    """Converts all files with '.txt' or '.pdf' extension in 'TestDocs' folder to JSON formatted Bag of Word dictionaries in 'Processed' folder (_BoW files)"""
    with os.scandir("TestDocs") as items:
        for item in items:

            #open .txt file and read, clean and correct text then create Bag of Words (Dictionary)
            if item.name[-4:] == ".txt":
                print("Processing: ", item.name, "....")
                myfile = open(r"TestDocs/" + item.name, encoding='utf-8')
                txt = myfile.read()
                doc = nlp(cleanText(txt))
                NLPBoW = NLPcreateBagOfWords(doc)
                NLPBoN = NLPcreateBagOfNumbers(doc)

                #save BoW as a _BoW file in JSON format
                saveFile = open(r"Processed/" + item.name[0:-4] + "_BoW", "w")
                json.dump((NLPBoW,NLPBoN), saveFile)

                myfile.close()
                saveFile.close()

            # open .pdf file and read, clean and correct text then create Bag of Words (Dictionary)
            elif item.name[-4:] == ".pdf":
                print("Processing: ", item.name, "....")

                txtList = extractTextPDF("TestDocs/" + item.name)
                BoWList = []

                for i in range(len(txtList)):
                    doc = nlp(cleanText(txtList[i]))
                    NLPBoW = NLPcreateBagOfWords(doc)
                    NLPBoN = NLPcreateBagOfNumbers(doc)

                    #add each page (BoW, BoN tuple) to List for saving to file later
                    BoWList.append((NLPBoW,NLPBoN))

                #save BoWList as a _BoW file in JSON format
                saveFile = open(r"Processed/" + item.name[0:-4], "w")
                json.dump(BoWList, saveFile)
                saveFile.close()

            else:
                print("In function 'processDocs' -",item.name, "not a .txt or .pdf")


def createLibrary():

    docList = []
    with os.scandir("Processed") as items:
        for item in items:
            f = open(r"Processed/" + item.name, "r")
            data = json.load(f)
            f.close()

            doc = Document(item.name, data[0][0])
            for page in data[1:]:
                #page[1] here would be the dictionary of numbers from the document.
                doc.addPage(page[0])

            docList.append(doc)

            library = DocumentCollection(docList[0])
            for doc in docList[1:]:
                library.addDoc(doc)

    return library

def processInput(text, nlp):
    """take raw text (text) and process to output list of lemmatised and lower case words"""
    addLog("Search Conducted", text )
    searchWords = []
    NLPtext = nlp(text)
    for token in NLPtext:
        searchWords.append(token.lemma_.lower())

    return searchWords

def displayWordcloud(text):
    wordcloud = WordCloud(width=3000, height=2000, random_state=1,
                          collocations=False).generate(text)

    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()
