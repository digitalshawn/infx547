#! /usr/bin/python
# coding: utf-8
""" 
Script to process tweets via stdin, expand URLs, add counts of urls/hashtags/mentions, and list of hashtags/mentions.

"""

import sys
sys.path.append('.')

import simplejson
import re
import time
from datetime          import datetime, timedelta
from email.utils       import parsedate_tz
from some_url_expander import URLError
from some_url_expander import APIError
from some_url_expander import URLExpander
from urlparse          import urlsplit

# who is expanding urls on our server
expander = URLExpander('SoMe_Lab_UW')

# List of punct to remove from string for track keyword matching
punct = re.escape('!"$%&\'()*+,-./:;<=>?@[\\]^`{|}~')

# List of words we are tracking
track_list = ["15o","15oct","99percent","acampadamataro","acampvalladolid","acampvalladolid","frankietease","ioccupy","ioccupyoccupyashland","k8_revolution","lakajo97","occopywmpt","occuponsmontrea","occupy","occupyaarhus","occupyabilene","occupyadelaide","occupyafrica","occupyafrica1","occupyakron","occupyalbany","occupyalbanyny1","occupyallentown","occupyamsterdam","occupyanchorage","occupyannarbor","occupyappleton","occupyarcata","occupyarizona","occupyarkansas","occupyashland","occupyashlandky","occupyaspen","occupyastoria","occupyathens","occupyathensga","occupyatl","occupyatlanta","occupyatlanticcity","occupyatlcity","occupyauburn","occupyaugusta","occupyaurora","occupyaustin","occupyb0ulder","occupybaltimore","occupybhgrove","occupybkny","occupyboise","occupyboulder","occupyboulderco","occupybrisbane","occupybrussels","occupybucharest","occupybuffalo","occupycarsoncty","occupycc","occupycha","occupychi","occupychicago","occupychucktown","occupycincinnati","occupycincy","occupyclarksvil","occupycleveland","occupycolumbia","occupycosprings","occupycu","occupycville","occupydallas","occupydc","occupydelaware","occupydenhaag","occupydenmark","occupyearth","occupyeugene","occupyflorida","occupyfm","occupyfortmyers","occupyftcollins","occupygtown","occupyhardford","occupyhartford","occupyhouston","occupyhsv","occupyhumboldt","occupyindy","occupyisu","occupyitaly","occupyjax","occupykeene","occupykelowna","occupykingston","occupyla","occupylansing","occupylasvegas","occupylausd","occupylondon","occupylsx","occupymadison99","occupymartnsbrg","occupymemphis","occupymia","occupymilwaukee","occupymn","occupymontrea","occupynashville","occupynewportor","occupynj","occupyns","occupyobise","occupyokc","occupyomaha","occupyorlando","occupyorlandofl","occupyottawa","occupypei","occupyphoenix","occupyportland","occupyprov","occupyquebec","occupyraleigh","occupyredlands","occupyrichmond","occupyroanokeva","occupyrockford","occupysacto","occupysalem","occupysananto","occupysanjose","occupysantacruz","occupysarasota","occupysarasotaoccupysanjose","occupysaskatoon","occupysb","occupysd","occupyseattle","occupysenhaag","occupyslc","occupysr","occupystaugust","occupystl","occupytampa","occupythemedia","occupytoronto","occupyueg","occupyukiah","occupyvermont","occupyvictoria","occupywallst","occupywallstnyc","occupywallstreet","occupywinnipeg","occupywmpt","occupywv","occupyyakima","occupyyeg","occupyyork","occupy_albanyny","occupy_okc","occupy_ottawa","occypyftcollins","ows","owslosangeles","owsspacecoast","perversmas","quimbanda","storydoula","tokumtorgin","nov5","5nov","bofa","cabincr3w","nov2","2nov","generalstrike","oct29","29oct","nov17","17nov","occupypics","usdor","occupydenver","needsoftheoccupiers","wearethe99","occupyoakland","occupyboston","occupy_boston","oo","53percent","1percent","banktransferday","moveyourmoney","louderthanwords","rebuilddream","acorn","n17","17n","d21","12d","occupyarrests","n30","30n","nov30","strike","occupytheport"]
# Turn it into a set
track_set = set(track_list)

# Parse Twitter created_at datestring and turn it into 
def to_datetime(datestring):
	time_tuple = parsedate_tz(datestring.strip())
	dt = datetime(*time_tuple[:6])
	return dt

# Loop over all lines recieved via stdin
for line in sys.stdin:
	
	line = line.strip()

	try:
		tweet = simplejson.loads(line)
		
		if (tweet.has_key("entities") and "text" in tweet):
			
			# Insert Counts
			tweet['counts'] = {
                                'urls': len(tweet['entities']['urls']), 
                                'hashtags': len(tweet['entities']['hashtags']), 
                                'user_mentions': len(tweet['entities']['user_mentions'])
                                };

			tweet['hashtags'] = []
			tweet['mentions'] = []

			# Insert list of hashtags and mentions
			for index in range(len(tweet['entities']['hashtags'])):
				tweet['hashtags'].append(tweet['entities']['hashtags'][index]['text'].lower())
			for index in range(len(tweet['entities']['user_mentions'])):
				tweet['mentions'].append(tweet['entities']['user_mentions'][index]['screen_name'].lower())

			tweet['hashtags'].sort()
			tweet['mentions'].sort()

                        # begin url expansion
			for index in range(len(tweet['entities']['urls'])):
				ourl = tweet['entities']['urls'][index]['expanded_url']

                                # if the expanded_url field is empty, try expanding the 'url' field instead
				if ourl is None:
					ourl = tweet['entities']['urls'][index]['url']

				if ourl:

					try:
						expanded = expander.Expand(ourl)
						json_api = simplejson.loads(expanded)
						if json_api:
							try:
								urlComponents = urlsplit(json_api['long-url'])
								domain = urlComponents.netloc
								tweet['entities']['urls'][index]['domain']=domain
							except AttributeError:
								pass
						tweet['entities']['urls'][index].update(json_api)

					# Catch any exceptions related to URL or expanding errors	
                                        # and make sure we record why
					except (URLError, APIError, UnicodeWarning, UnicodeError) as e:
						tweet['entities']['urls'][index]['expansion_error'] = e.msg;
                                        # this catches errors which seem to emanate from unicode errors
                                        # this should be checked on occasion to ensure it really is a unicode error
					except KeyError as e:
						tweet['entities']['urls'][index]['expansion_error'] = "Possible Unicode Error";
                        # end url expansion

                        # Track rule matches
                        tweet['track_kw'] = {}
                        tweet['track_kw']['hashtags'] = list(set(tweet['hashtags']).intersection(track_set))
                        tweet['track_kw']['mentions'] = list(set(tweet['mentions']).intersection(track_set))
                        tweet_text = re.sub('[%s]' % punct, ' ', tweet['text'])
                        tweet_text = tweet_text.lower().split()
                        tweet['track_kw']['text'] = list(set(tweet_text).intersection(track_set))

                        # Convert dates
			#tweet['created_ts'] = to_datetime(tweet['created_at'])
			#tweet['user']['created_ts'] = to_datetime(tweet['user']['created_at'])
			
		# Print tweet as JSON to stdout
		print simplejson.dumps(tweet)

	# Looks like the line wasn't valid JSON
	except ValueError:
		print "tweet not processed (ValueError): "+ line
		pass
	except KeyError:
		print "tweet not processed (KeyError): " + line
		pass
	except TypeError:
		print "tweet not processed (TypeError): " + line
		pass