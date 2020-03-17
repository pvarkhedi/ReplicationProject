#!/usr/bin/env python

import pandas as pd
import numpy as np
import requests
import py7zr
import shutil
from urllib.request import urlopen
from bs4 import BeautifulSoup
from py7zr import unpack_7zarchive
from lxml import etree
import lxml
from copy import deepcopy
import matplotlib.pyplot
import zipfile
import wget
import matplotlib.pyplot as plt
import re
import json
import sys
shutil.register_unpack_format('7zip', ['.7z'], unpack_7zarchive)


def createFilesFromWebsite(filename):
    #Opens up the url where the datasets are 
    url = "https://dumps.wikimedia.org/enwiki/20200101/"
    html = urlopen(url)

    #Creates a BeautifulSoup object to store the 
    soup = BeautifulSoup(html, 'lxml')
    title = soup.title

    all_links = soup.find_all("a")
    
    i = 0

    #loop through the first 3 links on the website
    for link in all_links[127:130]:   #127-137
        url = 'https://dumps.wikimedia.org/' + link.get("href")

        #downloads the file from the website url
        wget.download(url, filename + str(i) + '.7z')

        #unzips the .7z file 
        shutil.unpack_archive(filename + str(i) + ".7z")

        i = i + 1


def createLD (page):
    allDict = {}
    textDict = {}
    revision_count = 0
    LDlist = []
    outF = open("myOutFile.txt", "a")
    
    for elem in page.getiterator():
        if "title" in elem.tag:  
            outF.write(elem.text)
            outF.write("\n")
            
        if "revision" in elem.tag:
            revisionDict = {}
        
            for first in elem:
                
                if "id" in first.tag and "parentid" not in first.tag:
                    revisionDict["id"] = first.text
                    allDict[int(first.text)] = revision_count
                    
                if "timestamp" in first.tag:
                    revisionDict["timestamp"] = first.text
                    
                if "parentid" in first.tag:
                    revisionDict["parent_id"] = first.text
                    
                if "contributor" in first.tag:
                    for second in first:
                        if "username" in second.tag:
                            revisionDict["username"] = second.text
                if "text" in first.tag:
                    if first.text not in textDict:
                        textDict[first.text] = str(revision_count)
                        revert = "0"
                        versionNum = str(revision_count)
                    else:
                        revert = "1"
                        versionNum = textDict[first.text]
                    
            if "username" not in revisionDict:
                revisionDict["username"] = ""
            
            LDlist.append(("^^^" + str(revisionDict["timestamp"]) + " " + str(revert) + " " + str(versionNum) + " " + str(revisionDict["username"])))
            if revert == "0":
                revision_count = revision_count + 1
            
    for line in reversed(LDlist):
        outF.write(line)
        outF.write("\n")

        
def createLDfromTree(context):
    '''loops through an XML object, and writes 1000 page elements per file.'''
    page_num = 0
    count = 0
    
    outFile = open("myOutFile.txt", "w")
    for event, elem in context:
        if page_num % 1 == 0:
            for element in elem.getiterator():
                if "title" in element.tag:
                    createLD(elem)
        elem.clear()        
        
        
def computeM(reverts, mutualNum, numEdits):
    if len(reverts) == 0:
        return 0
    
    summedEdits = 0
    for tup in reverts:
        summedEdits = summedEdits + min(numEdits[tup[0]], numEdits[tup[1]])
        
    return len(mutualNum) * summedEdits


def getRevertedPairs(tuples):
    if len(tuples) == 0:
        return {}
    
    countMutualReverts = {}
    alreadyChecked = []
    
    for tup in tuples:
        
        if tup in alreadyChecked:
            continue
        if (tup[1], tup[0]) in alreadyChecked:
            continue
        alreadyChecked.append(tup)
        
        for possibleMutual in tuples:
            if possibleMutual == (tup[1], tup[0]):
                if tup in countMutualReverts:
                    countMutualReverts[tup] = countMutualReverts[tup] + 1
                else:
                    countMutualReverts[tup] = 1
                
    return countMutualReverts


def createDictionaries(edits):
    #dictionary of number of edits per editor
    numEdits = {}
    
    #dictionary of the editors of the version
    versionEditor = {}
    
    for key in sorted(edits.keys(), reverse = True):
        timestamp = edits[key][0]
        if edits[key][2] != "":
            revert = int(edits[key][1])
        else:
            continue
        if edits[key][2] != "":
            version = int(edits[key][2])
        else:
            continue
        editor = edits[key][3]
        
        #add to dictionary of number of edits
        if editor in numEdits:
            numEdits[editor] = numEdits[editor] + 1 
        else:
            numEdits[editor] = 1
            
        #keep track of original editors 
        if revert == 0:
            versionEditor[version] = editor
                
    return numEdits, versionEditor


def calculateM (edits, m):
    title = edits["title"]
    del edits['title']
    numEdits, versionEditor = createDictionaries(edits)    

    #create pairs of reverts
    tuples = []
    for key in sorted(edits.keys(), reverse = True):
        timestamp = edits[key][0]
        if edits[key][2] != "":
            revert = int(edits[key][1])
        else:
            continue
        if edits[key][2] != "":
            version = int(edits[key][2])
        else:
            continue
        editor = edits[key][3]
        
        if revert == 1:
            try:
                competitor = versionEditor[version + 1]
                tuples.append((editor, competitor))
            except:
                continue
    
    #find reverted pairs
    numOfMutualPairs = getRevertedPairs(tuples)
    
    #compute the m statistic
    m = computeM(tuples,numOfMutualPairs, numEdits)
    #add M statistic for this topic to dictionary
    return m


def createData():
    full_link = 'http://wwm.phy.bme.hu/LD/ld_en_wiki.zip'
    wget.download(full_link, "ld_en_file.zip")

    with zipfile.ZipFile('ld_en_file.zip',"r") as zip_ref:
        zip_ref.extractall("en_light_dump.txt")
        
        
def getM(file):
    #create a dictionary for all the M statistics
    mDict = {}

    #read in the first topic
    topicDict = {}
    topicDict["title"] = file.readline()

    #loop throough all lines in the dictionary
    editNum = 0
    numTopics = 0
    for line in file:
        if numTopics == 500:
            break 
            
        #if next topic is reached then calculate M statistic on current topic
        if line[0] != "^":
            topicDictNew = topicDict.copy()
            m = calculateM(topicDictNew, mDict)   
            mDict[topicDict["title"]] = m
            
            #reset dictionary for next topic
            topicDict = {}
            topicDict["title"] = line.strip("\n").strip(" ")
            editNum= 0
            numTopics = numTopics + 1
        #keep adding all edits to dictionary
        else:
            topicDict[editNum] = line.split(" ")

        editNum = editNum + 1

    #calculate M for the last topic in file
    topicDictNew = topicDict.copy()
    m = calculateM(topicDictNew, mDict)   
    mDict[topicDict["title"]] = m
    
    print("Top 20:")
    count = 0
    top = sorted(mDict.items(), key=lambda x: x[1], reverse = True)  
    for tup in top:
        if count == 20:
            break
        print(tup)
        count = count + 1
        
    print("Bottom 20:")
    count = 0
    top = sorted(mDict.items(), key=lambda x: x[1])  
    for tup in top:
        if count == 20:
            break
        print(tup)
        count = count + 1
        
    #close the file 
    file.close()
    

    

def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)
    return param

TEST_PARAMS = 'config/test-params.json'
DATA_PARAMS = 'config/data-params.json'

def main(targets):

    #create raw data files AND create Light Dump Files from them
    #DO NOT USE LIGHTLY - it will take a long time and space to download raw unzipped data
    if 'rawToLD' in targets:
        createFilesFromWebsite("testFile") 
        cfg = load_params(DATA_PARAMS)
        
        for file in cfg["RawData"]:
            context = etree.iterparse(file, tag='{http://www.mediawiki.org/xml/export-0.10/}page', encoding='utf-8')
            createLDfromTree(context)
        
    #test calculating M statistc from Light Dump Data    
    if 'testLdToM' in targets:
        cfg = load_params(TEST_PARAMS)

        for file in cfg["testLD"]:
            file = open(file, "r")
            getM(file)
        
    #test calculting M value
    #DO NOT USE LIGHTLY- second file takes a long time to run
    if 'LdToM' in targets:
        cfg = load_params(DATA_PARAMS)

        for file in cfg["LD"]:
            file = open(file, "r")
            getM(file)
    return

if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)