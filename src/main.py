import praw
import time
import os
import json
from configparser import ConfigParser
# import re
# from collections import OrderedDict

# To Do List
# Check multiple subs
# Animate appearance and disappearance of new fields

config = ConfigParser()
config.read('settings.cfg')

# Set parameters
# amount of time a story has to reach the top stories
hoursThreshold = int(config['Parameters']['HOURS_THRESHOLD'])
# number of hours a story can stay after its creation
expiration = int(config['Parameters']['EXPIRATION'])
# number of requests to ask for from each sub
rankThreshold = int(config['Parameters']['RANK_THRESHOLD'])
# Subreddits to check
subList = [config['Parameters']['SUBREDDIT']]
storyPath = config['Parameters']['STORY_PATH']


# Check for dictionary object
def initDict(path):
    """Check for json object. If it does not exist, create it."""
    if os.path.exists(path):
        with open(path, 'r') as fh:
            return json.load(fh)
    else:
        return {}


def authenticate():
    # Create reddit object to interact with server
    return praw.Reddit(client_id=config['Credentials']['CLIENT_ID'],
                       client_secret=config['Credentials']['CLIENT_SECRET'],
                       password=config['Credentials']['PASSWORD'],
                       user_agent=config['Credentials']['USER_AGENT'],
                       username=config['Credentials']['USERNAME'])


def getSub(reddit, sub, rankThreshold):
    # Grab subreddit content
    subreddit = reddit.subreddit(sub)
    hot_python = subreddit.hot(limit=rankThreshold)
    # Check for stickied posts
    i = 0
    for submission in hot_python:
        if submission.stickied:
            i += 1
    hot_python = subreddit.hot(limit=rankThreshold + i)
    return hot_python


def makeDict(hot_python, subDict, hoursThreshold):
    # Make index to check if stories already exist
    ind = [subDict[x]['url'] for x in subDict.keys()]
    # Fetch new headlines
    for submission in hot_python:
        if (time.time() - submission.created_utc) < (3600 * hoursThreshold) \
                and not submission.stickied:
            n = {'title': submission.title,
                 'created': submission.created_utc,
                 'domain': submission.domain,
                 'url': submission.url,
                 'permalink': 'https://www.reddit.com' + submission.permalink}
            if n['url'] not in ind:
                subDict[n['url']] = n
    return subDict


def cleanDict(subDict, expiration):
    # Clean up old entries after `expiration` hours has elapsed
    newDict = {}
    for k in subDict.keys():
        elapsed = time.time() - subDict[k]['created']
        expired = elapsed > (60 * 60 * expiration)
        if not expired:
            newDict[k] = subDict[k]
    return newDict


def orderDict(subDict):
    newDict = {}
    ind = [subDict[x]['created'] for x in subDict]
    ind.sort(reverse=True)
    for k in subDict:
        newDict[ind.index(subDict[k]['created'])] = subDict[k]
    return newDict


def saveDict(subDict, path):
    # Save file to output
    with open(path, 'w') as fh:
        json.dump(subDict, fh)


# Main Program
subDict = initDict(storyPath)
reddit = authenticate()

for s in subList:
    subObj = getSub(reddit, s, rankThreshold)
    subDict = makeDict(subObj, subDict, hoursThreshold)

subDict = cleanDict(subDict, expiration)
subDict = orderDict(subDict)
saveDict(subDict, storyPath)
