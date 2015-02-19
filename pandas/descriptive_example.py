
# coding: utf-8

## Descriptive Stats of Tweet File

# Load the necessary libraries

# In[3]:

get_ipython().magic('pylab inline')
import matplotlib.pyplot as plt
import pandas as pd
import simplejson
from collections import Counter


# The following code loops through the file with Twitter JSON. Since pandas doesn't like to work with nested dictionaries, we pull out the nested metadata we want to analyze before creating the data frame.

# In[76]:

file = open('/var/data/example_tweets.json')
tweets = []

# Create a counter of users, hashtags, URLs
users = Counter()
hashtags = Counter()
mentions = Counter()

for line in file:
    # Load each line of JSON
    tweet = simplejson.loads(line)
    if 'user' in tweet:
        users.update({tweet['user']['screen_name']:1})

        tweet['screen_name'] = tweet['user']['screen_name']

        # Pull out the user's followers_count
        tweet['followers_count'] = tweet['user']['followers_count']

        # Convert the text timestamp to a datetime object
        tweet['created_at'] = pd.to_datetime(tweet['created_at'])

        # Create a list of hashtags
        for ht in tweet['entities']['hashtags']:
            # Why do we want to lowercase the hashtags?
            hashtags.update({ht['text'].lower(): 1})
            
        tweet['hashtag_count'] = len(tweet['entities']['hashtags'])

        # Create a list of mentions
        tweet['mentions'] = []
        for mention in tweet['entities']['user_mentions']:
            mentions.update({mention['screen_name']:1})
        
        tweet['mention_count'] = len(tweet['entities']['user_mentions'])

        # Create a list of urls
        tweet['url_count'] = len(tweet['entities']['urls'])

        # Append the modified tweet to our array of tweets
        tweets.append(tweet)
df = pd.DataFrame(tweets)


## Descriptive Stats

##### 1. Graph the volume of tweets over time.

# In[138]:

df.created_at.groupby([df.created_at.dt.hour]).agg('count').plot()


# In[134]:

df.created_at.dt.hour.value_counts()


##### 2. Total number of tweets

# In[53]:

len(df)


##### 3. Total number of unique users

# In[54]:

df['screen_name'].nunique()


##### 4. Total number of unique hashtags

# In[55]:

len(hashtags)


##### 5. Graph of follower counts

# In[152]:

df.followers_count.value_counts().plot()


##### 6. Number of URLS in each tweet with histogram

# In[130]:

df.url_count.hist()


# In[149]:

df.url_count.value_counts()


##### 7. Number of hashtags in each tweet with histogram

# In[148]:

df.hashtag_count.hist()


# In[129]:

df.hashtag_count.value_counts()


##### 8. Top 20 users mentioned

# In[72]:

mentions.most_common(20)


##### 9. Top 10 hashtags besides #debates

# In[75]:

# Using the list of hashtags we created above
hashtags.most_common(21)[1:]


# In[ ]:



