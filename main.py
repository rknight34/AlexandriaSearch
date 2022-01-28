import spacy
import time
import pickle
import PySimpleGUI as sg


# requires following in terminal
# python -m spacy download en_core_web_lg


# My Modules
#from log import addLog
#from Alexandria import Document, DocumentCollection
from Util import *


def setupGUI():
    """Sets up the GUI window layout"""

    layout = [[sg.Text("Search Terms")],
              [sg.Input(key='-INPUT-')],
              [sg.Text(size=(60, 1), key='-OUTPUT1-'),sg.Button('OPEN FILE', key='_Open1_'),sg.Button('OPEN SIMILAR', key='_OpenSim1_'),sg.Button('WORD CLOUD', key='_Wordcloud1_')],
              [sg.Text(size=(60, 1), key='-OUTPUT2-'),sg.Button('OPEN FILE', key='_Open2_'),sg.Button('OPEN SIMILAR', key='_OpenSim2_'),sg.Button('WORD CLOUD', key='_Wordcloud2_')],
              [sg.Button('SEARCH', key='_Search_', bind_return_key=True), sg.Button('Quit'), sg.Button('Process Documents',key='_Process_')]]

    # Create the window
    window = sg.Window('Search in Docs', layout)

    return window


if __name__ == '__main__':

    start = time.process_time()

    #load the NLP model
    nlp = spacy.load("en_core_web_lg")

    print("Time taken for nlp model load:", time.process_time() - start)

    start = time.process_time()

    #load 'library' object from pickled file for speed of setup
    file = open('library_pickled', 'rb')
    library = pickle.load(file)
    file.close()

    #some diagnostic functions
    print ("Number of unique words in document library: ", len(library.masterDict))



    #setup GUI and return handle for event loop below
    window = setupGUI()

    #setup variable for opening file
    result1 = None
    result2 = None

    print("Time taken for setup:", time.process_time() - start)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        if event == '_Search_':
            start = time.process_time()

            #pre-process the user input search text
            searchWords = processInput(values['-INPUT-'], nlp)
            print("Searching for the tokens: ", searchWords)

            #request the ordered list of documents from search term
            searchList = library.search(searchWords)

            #update current search outputs
            result1 = searchList[0][0] # this is a docID in the library
            result2 = searchList[1][0] # this is a docID in the library
            doc1 = library.myDocs[result1]  # this is the actual doc
            doc2 = library.myDocs[result2]  # this is the actual doc

            #output to GUI - The +1 is due to page numbers being stored in array as elements (starting 0)
            if searchList[0][1] == 0:
                window['-OUTPUT1-'].update("Search words not found - try a different search")

            else:
                window['-OUTPUT1-'].update(str(doc1.myName) + " - 100%" + "        " +
                                       "Page " + str(doc1.search(searchWords)[-1][0] + 1))

                match = round(searchList[1][1] / searchList[0][1] * 100)

                window['-OUTPUT2-'].update(str(doc2.myName) + " - " + str(match) + "%" + "        " +
                                       "Page " + str(doc2.search(searchWords)[-1][0] + 1))

            print("Time taken for search:", time.process_time() - start)

        # Open the file in default viewer
        if event == '_Open1_':
            if result1 != None:
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(doc1.myName) +".pdf")

        # Open the file in default viewer
        if event == '_Open2_':
            if result2 != None:
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(doc2.myName) +".pdf")

        if event == '_OpenSim1_':
            if result1 != None:
                similarDoc1 = library.myDocs[library.getSimilarList(result1)[0][0]]
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(similarDoc1.myName) +".pdf")

        if event == '_OpenSim2_':
            if result2 != None:
                similarDoc2 = library.myDocs[library.getSimilarList(result2)[0][0]]
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(similarDoc2.myName) +".pdf")

        if event == '_Wordcloud1_':
            if result1 != None:
                displayWordcloud(doc1.returnTextStringOfUniqueWordsFrequency())

        if event == '_Wordcloud2_':
            if result2 != None:
                displayWordcloud(doc2.returnTextStringOfUniqueWordsFrequency())

        if event == '_Process_':
            #take all documents in 'TestDocs' and pre-process into 'Processed' folder
            processDocs(nlp)

            #need to update the library and save it to pickle file for later access
            library = createLibrary()
            libraryFile = open('library_pickled', 'wb')
            pickle.dump(library, libraryFile)
            libraryFile.close()

    # Finish up by removing from the screen
    window.close()
