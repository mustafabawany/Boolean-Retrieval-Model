from flask import Flask, render_template, url_for, request
from flask_sqlalchemy import SQLAlchemy
import nltk
import os
import re
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

app = Flask(__name__)


@app.route("/" , methods=['POST' , 'GET'])

def test():
    if request.method == "POST":
        Query = request.form['query']
        queryType = 0
        for word in Query:
            if ("/" in word):
                queryType = 1

        """Boolean Query"""

        if (queryType == 0):

            QueryWords = word_tokenize(Query)

            """If NOT is at first position"""
            notIndex = 0
            if "NOT" in QueryWords:
                if QueryWords.index("NOT") == 0:
                    notIndex = 1     
        
            """Checking Operation Sequence / Sequence of AND , OR , NOT.""" 
            operationSequence = []
            for operations in QueryWords:
                if operations == "AND" or operations == "OR" or operations == "NOT":
                    operationSequence.append(operations)
                
            if (len(operationSequence) == 0):
                operationSequence.append("AND")
            

            """------------------------------Query Pre Processing----------------------------------"""
            
            
            """Removing OR from query since it is not being treated as stop word"""
            QueryWords = word_tokenize(Query)
            QueryProcessed1 = [word for word in QueryWords if (word != "OR" and word != "NOT")]
            QueryProcessed1 = ' '.join(QueryProcessed1)
            QueryProcessed1 = QueryProcessed1.lower()

            """Removing Punctuations"""
            QueryProcessed2 = removePunctuations(QueryProcessed1)
            
            """Removing Stop Words"""
            QueryProcessed3 = removeStopWords(QueryProcessed2)
            
            """Applying Porter Stemmer"""
            QueryProcessed4 = stemSentence(QueryProcessed3)

            """Seperating Hyphenated words"""
            QueryProcessed5 = removeHyphenatedWords(QueryProcessed4)

            """Searching for posting lists of each word in query"""
            DocumentList = []
            DocumentList = searchInDictionary(QueryProcessed5)
            resultSet = {}
            Set1 = set(DocumentList[0])

            Unionlist = []
            for i in range(1,449):
                Unionlist.append(i)

            unionSet = set(Unionlist)

            """------------------------Combing the results and providing final result--------------------"""
            
            if (notIndex == 1):
                print(operationSequence.pop(0))
                Set1 = unionSet.difference(Set1)

            for i in range(len(DocumentList) - 1):
                Set2 = set(DocumentList[i+1])
                if (operationSequence[i] == "AND"):
                    Set1 = Set2.intersection(Set1)
                elif (operationSequence[i] == "OR"):
                    Set1 = Set2.union(Set1)
                elif (operationSequence[i] == "NOT"):
                    Set2 = unionSet.difference(Set2)
                    Set1 = Set2.intersection(Set1)

            if (len(Set1) == 0):
                return "No Documents Found!"
            else:   
                resultSet = sorted(Set1)
                result = ""
                resultDictionary = dict()
                for docNo in resultSet:
                    with open(os.getcwd() + "/Abstracts/" + str(docNo) + ".txt", encoding="utf8" , errors="ignore") as fileHandle:
                        plainSentence = fileHandle.read()
                        resultDictionary[str(docNo)] = plainSentence
                
                return render_template('result.html' , result=resultDictionary , Query=Query)
        
        else:

            """------------------------------Query Pre Processing----------------------------------"""
            
            """Removing Position from query"""
            QueryProcessed1 = ""
            for i in range (len(Query)):
                if Query[i] == "/":
                    searchingPositions = Query[i+1]
                    break
                else:
                    QueryProcessed1 = QueryProcessed1 + Query[i] 
            
            """Lower Casing Query Terms"""
            QueryProcessed1 = QueryProcessed1.lower()

            """Removing Punctuations"""
            QueryProcessed2 = removePunctuations(QueryProcessed1)

            """Removing Stop Words"""
            QueryProcessed3 = removeStopWords(QueryProcessed2)
            
            """Applying Porter Stemmer"""
            QueryProcessed4 = stemSentence(QueryProcessed3)
            
            """Seperating Hyphenated words"""
            QueryProcessed5 = removeHyphenatedWords(QueryProcessed4)
            print(QueryProcessed5)


            """Searching for posting lists and Positions of each word in query"""
            DocumentList = []
            DocumentList = searchInPositionalIndex(QueryProcessed5)
            finalResult = PositionalIntersect(DocumentList, int(searchingPositions))
            resultDictionary = dict()
            for docNo in finalResult:
                with open(os.getcwd() + "/Abstracts/" + str(docNo) + ".txt", encoding="utf8" , errors="ignore") as fileHandle:
                    plainSentence = fileHandle.read()
                    resultDictionary[str(docNo)] = plainSentence
            return render_template('result.html', result=resultDictionary , Query=Query)

    else:
        for docNo in range (1,449):
            docNo = str(docNo)
            with open(os.getcwd() + "/Abstracts/" + docNo + ".txt", encoding="utf8" , errors="ignore") as fileHandle:
                plainSentence = fileHandle.read()
            
            """----------------------------------Pre Processing Phase------------------------------"""
            
            """Lower casing words."""
            plainSentence = plainSentence.lower()

            """Removing punctuations."""
            preProcess1 = removePunctuations(plainSentence)

            """Removing Stop Words."""
            preProcess2 = removeStopWords(preProcess1)

            """Applying Porter Stemmer."""
            preProcess3 = stemSentence(preProcess1)

            """Seperating Hyphenated words."""
            preProcess4 = removeHyphenatedWords(preProcess3)

            """Creating Dictionary."""
            createDictionary(preProcess4, int(docNo))

            """Creating Positional Index"""
            createPositionalIndex(preProcess4, int(docNo))
        return render_template('index.html')


if __name__ == "__main__":
    ps = PorterStemmer()
    Dictionary = dict()
    PositionalIndex = dict()
    def stemSentence(sentence):
        token_words = word_tokenize(sentence)
        stem_sentence=[]
        for word in token_words:
            stem_sentence.append(ps.stem(word))
            stem_sentence.append(" ")
        return "".join(stem_sentence)

    def removeStopWords(sentence):
        stopWordsList = []
        tempFileHandle = open(os.getcwd() + "/Stopword-List.txt" , "r");
        stopWords = tempFileHandle.read()
        token_stopWord = word_tokenize(stopWords)
        for eachStopWord in token_stopWord:
            stopWordsList.append(eachStopWord)
        token_words = word_tokenize(sentence)
        resultSentence  = [word for word in token_words if word not in stopWordsList]
        resultSentence = ' '.join(resultSentence)
        return resultSentence

    def removePunctuations(sentence):
        punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
        newSentence = ""
        for word in sentence:
            if (word in punctuations):
                newSentence = newSentence + " "
            else: 
                newSentence = newSentence + word

        return newSentence

    def removeHyphenatedWords(sentence):
        token_words = word_tokenize(sentence)
        newSentence = []
        for word in token_words:
            if '-' in word:
                temp = []
                for character in word:
                    if character == '-':
                        temp.append(" ")
                    else :
                        temp.append(character)
                temp = "".join(temp)
                newSentence.append(temp)
                newSentence.append(" ")
            else: 
                newSentence.append(word) 
                newSentence.append(" ")
        return "".join(newSentence)

    """-----------------------------------------Positional Index-------------------------------------"""
    def createPositionalIndex(sentence , docNo):
        token_words = word_tokenize(sentence)
        wordPosition = 1
        for word in token_words:
            if word not in PositionalIndex:
                """If word is not in Positional Index"""
                docNumberList = dict()
                positions = []
                positions.append(wordPosition)
                docNumberList[docNo] = positions
                PositionalIndex[word] = docNumberList
                
            else:
                """If word is already in Positional Index"""
                predocList = dict()
                predocList = PositionalIndex[word]
                if docNo in predocList:
                    positions = predocList[docNo]
                    positions.append(wordPosition)
                    predocList[docNo] = positions
                    
                    PositionalIndex[word] = predocList
                elif docNo not in predocList:
                    positions = []
                    positions.append(wordPosition)
                    predocList[docNo] = positions
                    PositionalIndex[word] = predocList

            wordPosition = wordPosition + 1   

    def searchInPositionalIndex(Query):
        total_list = []
        tempDict = dict()
        token_words = word_tokenize(Query)
        for word in token_words:
            if word in PositionalIndex:
                tempDict = PositionalIndex[word]
                total_list.append(tempDict)
            else:
                print("Word not in dictionary")
        return total_list

    def PositionalIntersect(documentList, k):
        finalResult = []
        p1 = dict()
        p2 = dict()
        p1 = documentList[0]
        p2 = documentList[1]
        for docID in (p1.keys() and p2.keys()):
            if docID in p1.keys() and p2.keys():
                pp1 = p1[docID]
                pp2 = p2[docID]
                i = 0
                while(i < len(pp1) and i < len(pp2)):
                    if (pp1[i] > pp2[i]):
                        if ((pp1[i] - pp2[i]) <=(k+1)):
                            if docID not in finalResult:
                                finalResult.append(docID)
                    elif (pp1[i] < pp2[i]):
                        if ((pp2[i] - pp1[i]) <= (k+1)):
                            if docID not in finalResult:
                                finalResult.append(docID)
                    i = i + 1    
        return finalResult





    """------------------------------------------Inverted Index--------------------------------------"""
    def createDictionary(sentence , docNo):
        token_words = word_tokenize(sentence)
        for word in token_words:
            if word not in Dictionary:
                docList = []
                docList.append(docNo)
                Dictionary[word] = docList
            else:
                predocList = Dictionary[word]
                if docNo not in predocList:
                    docList = predocList
                    docList.append(docNo)
                    Dictionary[word] = docList

    def searchInDictionary(Query):
        total_list = []
        token_words = word_tokenize(Query)
        for word in token_words:
            if word in Dictionary:
                tempList = Dictionary[word]
                total_list.append(tempList)
            else:
                print("Word not in dictionary")
        return total_list
    app.run(debug=True)