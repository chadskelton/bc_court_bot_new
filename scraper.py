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
import mechanize

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
            # comment out to populate database so don't duplicate;  remove after first run
            api.update_status(status=statusupdate)
            time.sleep(60)
        except:
            print "Unable to add to table or tweet:"
            try:
                print record # to try to see what record couldn't be sent
            except:
                print "Couldn't display record"
            
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
        html = requests.get(url, verify=False) # added verify=False because of SSL Error
        htmlpage = html.content
        
        soup = BeautifulSoup(htmlpage)
        
        table = soup.find ("div", {"class" : "view-content"})
    
        decisions = table.findAll ("a")
        
        for decision in decisions:
            record = {}
            record["type"] = "B.C. Provincial Court"
            record["citation"] = decision.text
            badurl = decision.get('href')
            record["url"] = badurl.replace("/judgments.php?link=","")
            tweetit(record)
            
        
'''
def scrape_bcpc(url):
        
        # html = requests.get(url, verify=False, headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'})
        html = requests.get(url, verify=False)
        # verify=False because getting 502 errors due to invalid certificate
        htmlpage = html.content
        
        soup = BeautifulSoup(htmlpage)
        
        print soup
        
        table = soup.find ("div", {"class" : "view-content"})
        
        # print table
    
        decisions = table.findAll ("a")
        
        # decisions = soup.findAll ("div", {"class":"views-field views-field-text"})
        
        # new instructions for canlii site, commented out because no longer working
        
        
        print soup
        
        section = soup.find ("div", {"id" : "decisionsListing"})
        
        print section        
        
        decisions = section.findAll ("a")        
        
        print decisions
        
        for decision in decisions:
            record = {}
            record["type"] = "B.C. Provincial Court"
            record["citation"] = decision.text
            # badurl = decision.get('href')
            # record["url"] = badurl.replace("/judgments.php?link=","")
            record["url"] = 'https://www.canlii.org' + decision.get('href')
            tweetit(record)
'''            

            

for x in range (0, 15): # trying 15 instead of 21
    print "Cycle:" + str(x)
    time.sleep(3600)
    
    try:
        scrape_bcsc("https://www.bccourts.ca/supreme_court/recent_Judgments.aspx")
    except:
        print 'Difficulty scraping BCSC'

    try:
        scrape_bcca("https://www.bccourts.ca/court_of_appeal/recent_Judgments.aspx")
    except:
        print 'Difficulty scraping BCCA'

    try:
        scrape_bcpc("https://www.provincialcourt.bc.ca/judgments-decisions")
    except:
        print 'Difficulty scraping BCPC'
