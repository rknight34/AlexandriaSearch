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

