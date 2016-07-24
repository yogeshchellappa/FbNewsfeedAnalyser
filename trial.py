# Python script to auto-reply an acknowledgement and thank you to all posts on Facebook on the user's timeline recognizing Happy Birthday

import re
import random
import json
import webbrowser
import urllib
import urllib.request
import urllib.error
import urllib.parse
import datetime
import time
import sys


ACCESS_TOKEN = ''
ACCESS_URL = 'https://graph.facebook.com/'
USERNAME = ''

def getaccesstoken():
	"""
	Function to obtain an access token with the necessary permissions to access posts and reply back.
	"""
	permission = input("The script would like to access your Facebook account.\nPress y to continue and n to abort: \n")
	if(permission=='n'):
		sys.exit(1)
	elif(permission=='y'):
		print("To generate your token the script needs to access your feeds"
		      " and publishing permissions. Allow access in the web pages opening shortly"
		      " in your browser and then copy the token which is a long sequence of random"
		      " characters under the label \'Access Token:\', in the url opening following the first.")
		time.sleep(1)
		print("Opening links now...")
		time.sleep(2)
		webbrowser.open("https://www.facebook.com/dialog/oauth?"
                      "response_type=token&client_id=145634995501895&"
                      "redirect_uri=http://developers.facebook.com/tools/"
                      "explorer/callback&scope=user_birthday,publish_actions"
                      ",read_stream")
		time.sleep(10)
		webbrowser.open("http://developers.facebook.com/tools/explorer")
		print()
		access_token = input("Enter the access token obtained from API Explorer page: \n")
		return access_token
	else:
		print("Invalid input.")
		sys.exit(1)


def collect_data():
	"""
	Collects all the posts on your feed on the day of your most recent birthday and finds all the posts wishing you a happy birthday.
	"""
	print()
	print("Fetching data. Please wait...")
	try:
		datafile = urllib.request.urlopen(ACCESS_URL + 'me?fields=birthday&access_token=' + ACCESS_TOKEN)
	except urllib.error.URLError:
		print("Please verify the access token entered.")
		print("Exiting now...")
		time.sleep(1)
		sys.exit(1)
	except urllib.error.HTTPError:
		print("Check if you're connected to the internet.")
		print("Exiting now...")
		time.sleep(1)
		sys.exit(1)
	except:
		print("Unknown error.")
	
	
	bday = json.loads(datafile.read().decode("utf-8"))['birthday']
	datafile.close()

	# bday now contains your birthday now
		# eg, bday for me now holds '10/20/1993'
	
	# Now replacing the year field in 'bday' with current year, so that posts on your wall on that day are accessed.
	
	# All posts on that day and made with time greater than 11:55 pm are considered.
	bday = datetime.datetime.strptime(bday, '%m/%d/%Y')
	t = '23:55'
	t = t.split(':')
	
	# Subtracting a day from the birthday. Now we are at 11:55 pm the previous night. We start obtaining posts from this time.
	wish = bday.replace(year = datetime.datetime.now().year, hour = int(t[0]), minute = int(t[1])) - datetime.timedelta(days = 1) 
	
	# Converting into epoch time
	wish_timestamp = time.mktime(wish.timetuple())
	wish_timestamp = int(wish_timestamp)
	
	# Limiting the posts obtained only to the birthday.
	# Calculating time till midnight of the birthday. 
	nextday = wish_timestamp + ((24*60*60) + (5*60) )
	
	query = {'actors':('SELECT actor_id, post_id, message FROM stream WHERE source_id = me() AND created_time > %s AND created_time < %s LIMIT 200' % (wish_timestamp, nextday)), 'names': ('SELECT first_name,uid FROM user WHERE uid IN (SELECT actor_id FROM #actors)')}
	
	urlstring = {'access_token': ACCESS_TOKEN, 'q': query}
	fullurl = 'https://graph.facebook.com/fql' + '?' + urllib.parse.urlencode(urlstring)
	
	try:
		res = urllib.request.urlopen(fullurl)
	except:
		print("An error has occured.")
	result = json.loads(res.read().decode('utf-8'))
	res.close()
	
	
	post_list = result['data'][0]['fql_result_set']
	name_list = result['data'][1]['fql_result_set']
	messages = []
	
	

	# dict has actor_id and the corresponding actor name
	dict = {}
	for i in range(len(name_list)):
		dict[name_list[i]['uid']] = name_list[i]['first_name']
	
	
	# Getting all msgs and appending it to messages list
	for i in range(len(name_list)):
		msg = result['data'][0]['fql_result_set'][i]['message']
		messages.append(msg)
	
	# Case insensitive comparision	
	messages = [(i.lower()).strip() for i in messages]
	
	# Possible list of matching words 
	wishes = set(["happy", "birthday", "happie" ,"b'day", "bday", "returns"])
	
	# Pattern for regex:	
	wish = '[hH]?a+p+i*e*y+.*[bB]?i+r+t+h+d*a*y*'

	# List of dictionaries with post_id and first_name of the user for each post
	post_data = [{'post_id': post_list[i]['post_id'],'from':  dict[post_list[i]['actor_id']]} 
			for i in range(len(messages)) if((re.search(wish,messages[i])) or (wishes.intersection(set((messages[i]).split()))))]

	print("Successfully fetched data: ", len(post_data), "matching posts found.")
	print()
	return post_data
	

def reply_post(post_list):
	"""
	Replies to those posts which have been retrieved and comments a message from a pre-defined set
	and prints the user the number of friends who have wished him/her.
	"""
	
	# List of reply messages. One of these will be chosen at random for the reply.
	reply = ['Thank you :)']
	
	print("Replying to posts now. Please wait...")
	
	# Rather than creating multiple HTTP requests, we create a single batch request to send all the requests.
	batch = [{"method": "POST",
		  "relative_url": str(item['post_id'] + "/comments?message=" + 
		   reply[random.randint(0,len(reply))-1]).replace('[name]', item['from'])} 
		   for item in post_list]
	
	# Batch request for liking each of the posts
	like = [{"method": "POST",
		 "relative_url": str(item['post_id'] + "/likes")}
		  for item in post_list]
	
	post_data = urllib.parse.urlencode({'access token': ACCESS_TOKEN, 'batch': batch})
	like_data = urllib.parse.urlencode({'access token': ACCESS_TOKEN, 'batch': like})
	
	# Specifying the encoding format.
	post_data = post_data.encode('utf-8')
	like_data = like_data.encode('utf-8')
	
	try:
		datafeed = urllib.request.urlopen(ACCESS_URL, post_data)
		likefeed = urllib.request.urlopen(ACCESS_URL, like_data)
	except urllib.error.HTTPError:
		print("Please check your internet connection...")
		print("Terminating now.")
		sys.exit(1)
	except urllib.error.URLerror:
		print("Fatal error occured.")
		print('Terminating now.')
		sys.exit(1)
	except:
		print("Unknown error.")
		print("Terminating now.")
		sys.exit(1)
		
	response_list = json.loads(datafeed.read().decode('utf-8'))
	like_list = json.loads(likefeed.read().decode('utf-8'))
	datafeed.close()
	
	post_count = 0
	like_count = 0
	
	# status code value = 200 => OK
	for i in response_list:
		if i['code'] == 200:
			post_count += 1
	for i in like_list:
		if i['code'] == 200:
			like_count += 1
	if(like_count == post_count):
		print("Successfully liked and replied to %s post(s)!" % like_count)
	print()


## Client ##
ACCESS_TOKEN = getaccesstoken()
data = collect_data()
reply_post(data)		


