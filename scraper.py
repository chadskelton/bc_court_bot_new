#!/usr/bin/env python

# Load in modules
# !!! NOTE - When doing a more general News Bot, should probably create another field that describes the data
# (i.e. "New Court Decision") and one that has the email of the person to notify (as this may vary depending
# on the site scraped. Could then have one script grabbing dozens of different sites and notifying
# dozens of different reporters/editors !!!

import scraperwiki
import tweepy
import time
from datetime import datetime
import smtplib
import requests
from BeautifulSoup import BeautifulSoup
# new for secret variables
import os

# Establish Twitter authorization. These codes are specific to @BCCourtBot
# Think it's better to setup authorization at beginning instead of resetting within tweet function, but not sure

TWEEPY_CONSUMER_KEY = os.environ['MORPH_CONSUMER_KEY']
TWEEPY_CONSUMER_SECRET = os.environ['MORPH_CONSUMER_SECRET']
TWEEPY_ACCESS_TOKEN = os.environ['MORPH_ACCESS_TOKEN']
TWEEPY_ACCESS_TOKEN_SECRET = os.environ['MORPH_ACCESS_TOKEN_SECRET']

# Setup initial record
# removed after first run, don't think i need it once it's all setup

record = {}
record["type"] = "Test"
record["citation"] = "This is a test record"
record["url"] =  "http://vancouversun.com/"
scraperwiki.sqlite.save(['url'], record)


auth1 = tweepy.auth.OAuthHandler(TWEEPY_CONSUMER_KEY, TWEEPY_CONSUMER_SECRET)
auth1.set_access_token(TWEEPY_ACCESS_TOKEN, TWEEPY_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth1)

def tweetit(record): # both decides to tweet and whether to add to table

    if len(record["citation"]) > 65:
        CitationText = record["citation"][:65] + "..."
    else:
        CitationText = record["citation"]
        
    query = "SELECT count(*) FROM data WHERE url = '" + record["url"] + "'"
    count = scraperwiki.sqlite.execute(query)
    countcheck = count['data'][0][0]
    if countcheck > 0:
        print "Already in database"
        print record
    if countcheck == 0:
        try:
            print "New record"
            scraperwiki.sqlite.save(['url'], record)
            statusupdate = "New ruling from the " + record["type"] + " in '" + CitationText + "' " + record["url"]
            print statusupdate
            # commenting out to populate database so don't duplicate; will remove after first run
            # api.update_status(status=statusupdate)
            # time.sleep(30)
        except:
            print "Unable to add to table or tweet"
            
    # code to send out tweet based on the record dict that's sent to the function

def emailit(record): # can use this function if want to email update instead of tweet it

# !!! Important, way this is setup it will only email if it hasn't been tweeted; if want to do both; should add the
# email stuff to the tweet one !!!

    CitationText = record["citation"]
        
    query = "SELECT count(*) FROM swdata WHERE url = '" + record["url"] + "'"
    count = scraperwiki.sqlite.execute(query)
    countcheck = count['data'][0][0]
    if countcheck > 0:
        print "Already in database"
    if countcheck == 0:
        try:
            print "New record"
            scraperwiki.sqlite.save(['url'], record)
            
            # Writing the message
            
            fromaddr = 'sunnewsbot@gmail.com'
            toaddrs  = ['cskelton@vancouversun.com','cskeltonnews@gmail.com'] # or adrienne or bev
            msg = "Subject: New court ruling - " + record["citation"] + "\nTo: cskelton@vancouversun.com; cskeltonnews@gmail.com\n\nJust posted from " + record["type"] + ": '" + CitationText + "' " + record["url"]
            
            # Gmail login
            
            username = 'sunnewsbot'
            password = 'NOT SAYING'
            
            # Sending the mail 
            
            server = smtplib.SMTP("smtp.gmail.com:587")
            server.starttls()
            server.login(username,password)
            server.sendmail(fromaddr, toaddrs, msg)
            server.quit()
            
            time.sleep(30)
            
        except:
            print "Unable to add to table or email"
    
def scrape_bcsc(url): # in case page changes

    html = requests.get(url)
    htmlpage = html.content
    
    soup = BeautifulSoup(htmlpage)
    
    table = soup.find ("div", {"id" : "recentJudg"})

    decisions = table.findAll ("a")
    
    for decision in decisions:
        record = {}
        record["type"] = "B.C. Supreme Court"
        record["citation"] = decision.text
        record["url"] = 'http://www.courts.gov.bc.ca' + decision.get('href')
        tweetit(record)

def scrape_bcca(url):

    html = requests.get(url)
    htmlpage = html.content
    
    soup = BeautifulSoup(htmlpage)
    
    table = soup.find ("div", {"id" : "recentJudg"})

    decisions = table.findAll ("a", {"target" : "_blank"})
    
    for decision in decisions:
        record = {}
        record["type"] = "B.C. Court of Appeal"
        record["citation"] = decision.text
        record["url"] = 'http://www.courts.gov.bc.ca' + decision.get('href')
        tweetit(record)

def scrape_bcpc(url):
        html = requests.get(url)
        htmlpage = html.content
        
        soup = BeautifulSoup(htmlpage)
        
        table = soup.find ("div", {"class" : "view-content"})
        
        print table
    
        decisions = table.findAll ("a")
        
        for decision in decisions:
            record = {}
            record["type"] = "B.C. Provincial Court"
            record["citation"] = decision.text
            badurl = decision.get('href')
            record["url"] = badurl.replace("/judgments.php?link=","")
            tweetit(record)

try:
    scrape_bcsc("http://www.courts.gov.bc.ca/supreme_court/recent_Judgments.aspx")
except:
    print 'Difficulty scraping BCSC'
    
try:
    scrape_bcca("http://www.courts.gov.bc.ca/court_of_appeal/recent_Judgments.aspx")
except:
    print 'Difficulty scraping BCCA'
    
#try:
scrape_bcpc("http://www.provincialcourt.bc.ca/judgments-decisions")
#except:
#    print 'Difficulty scraping BCPC'
