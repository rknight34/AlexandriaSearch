import spacy
import time
import pickle
import PySimpleGUI as sg
import io

# requires following in terminal
# python -m spacy download en_core_web_lg

# My Modules
#from log import addLog
from Alexandria import Document, DocumentCollection, Alexandria

from Util import *


def setupGUI():
    """Sets up the GUI window layout"""

    layout = [[sg.Text("Search Terms")],
              [sg.Input(key='-INPUT-')],
              [sg.Text(size=(60, 1), key='-OUTPUT1-'),sg.Button('OPEN FILE', key='_Open1_'),sg.Button('OPEN SIMILAR', key='_OpenSim1_'),sg.Button('WORD CLOUD', key='_Wordcloud1_')],
              [sg.Text(size=(60, 1), key='-OUTPUT2-'),sg.Button('OPEN FILE', key='_Open2_'),sg.Button('OPEN SIMILAR', key='_OpenSim2_'),sg.Button('WORD CLOUD', key='_Wordcloud2_')],
              [sg.Button('SEARCH', key='_Search_', bind_return_key=True), sg.Button('Quit'), sg.Button('Process Documents',key='_Process_')],
              [sg.Combo(['choice 1', 'choice 2', 'choice 3'])]]

    # Create the window
    window = sg.Window('Search in Docs', layout)

    return window

def displayImage(title,image):
    layout = [[sg.Image(key="-IMAGE-")]]
    window = sg.Window(title, layout, finalize=True)
    image.thumbnail((900, 600))
    bio = io.BytesIO()
    image.save(bio, format="PNG")
    window["-IMAGE-"].update(data=bio.getvalue())

    return window

if __name__ == '__main__':

    #setup GUI and return handle for event loop below
    window = setupGUI()

    start = time.process_time()
    #create wrapper Alexandria object and pass nlp model
    Alex = Alexandria(spacy.load("en_core_web_lg"))
    print("Time taken for nlp model load:", time.process_time() - start)

    #load library (A DocumentCollection object) into Alexandria wrapper
    if Alex.loadLibraryFromPickle('library_pickled'):
        print ("Library loaded from file successfully")
    else:
        print ("Library not found, generating from scratch")
        Alex.processDocs("TestDocs")
        Alex.createLibrary()
        Alex.saveLibraryToPickle("library_pickled")

    #some diagnostic functions
    print ("Number of unique words in document library: ", len(Alex.library.masterDict))
    print ("Number of Documents in Library: ", len(Alex.library.myDocs))

    #setup variable for opening file
    result1 = None
    result2 = None

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        if event == '_Search_':
            start = time.process_time()

            #pre-process the user input search text
            searchWords = Alex.processInput(values['-INPUT-'])
            print("Searching for the tokens: ", searchWords)

            #request the ordered list of documents from search term
            searchList = Alex.library.search(searchWords)

            #update current search outputs
            result1 = searchList[0][0] # this is a docID in the library
            result2 = searchList[1][0] # this is a docID in the library
            doc1: Document = Alex.library.myDocs[result1]  # this is the actual doc
            doc2: Document = Alex.library.myDocs[result2]  # this is the actual doc

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
                similarDoc1 = Alex.library.myDocs[Alex.library.getSimilarList(result1)[0][0]]
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(similarDoc1.myName) +".pdf")

        if event == '_OpenSim2_':
            if result2 != None:
                similarDoc2 = Alex.library.myDocs[Alex.library.getSimilarList(result2)[0][0]]
                os.startfile("C:/Users/Hp/PycharmProjects/AlexandriaDocuments/TestDocs/" + str(similarDoc2.myName) +".pdf")

        if event == '_Wordcloud1_':
            if result1 != None:
                displayImage(doc1.myName + " Wordcloud", doc1.returnWordcloud())

        if event == '_Wordcloud2_':
            if result2 != None:
                displayImage(doc2.myName + " Wordcloud", doc2.returnWordcloud())

        if event == '_Process_':
            #take all documents in 'TestDocs' and pre-process into 'Processed' folder
            Alex.processDocs("TestDocs")

            #need to update the library and save it to pickle file for later access
            Alex.createLibrary()
            Alex.saveLibraryToPickle("library_pickled")

    # Finish up by removing from the screen
    window.close()
