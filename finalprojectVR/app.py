from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from watson_developer_cloud import VisualRecognitionV3
from flask_uploads import UploadSet, configure_uploads, IMAGES
from random import uniform
import json
import os
import datetime
import timeit


"""[summary]

A Python web app that runs locally.
This web app simulates a cash register check out system.
Features includes:
	1) Identifying produce such as fruits and vegetables that you would encounter while grocery shopping
	2) Able to identify that it is unable to identify a fruit or vegetable
	3) Can list up to 3 options of possible results where the user can pick to add to cart
	4) Grocery list summary to see what you have ordered, displaying total weight (geneated randomly), unit price per kg and total price for that item
	5) Displays a finish and pay screen to see total + tax (tax is 0 because produce doesn't have tax.)
	6) Dispalys current time 
	7) Displays a pop up help box
	8) Simulates a manual code enter pop up functionality

"""


## Watson Configurations ---------------------------------------------------------------------------
vr = VisualRecognitionV3(
	"2016-05-20",
	api_key="843909e8ab8cbe39596df5ff4725d8a0fdb5e756"
)

classifier_id = "Ringo_IdentifAIer_408586032"


## Flask Configurations ------------------------------------------------------------------------------
app = Flask(__name__)               	# creates an instance of Flask in app
app.config.from_object(__name__)    	# load config from this file , flaskr.py
photos = UploadSet("photos", IMAGES)

app.config.update(dict(
	SECRET_KEY='development key',
	UPLOADED_PHOTOS_DEST="static/image"
))
configure_uploads(app, photos)


## App Data -------------------------------------------------------------------------------------

# prices are listed in $/kg, referenced from loblaws online
PRICE_DATABASE = {
	"Pumpkin":4.00,
	"Fresh Hothouse Tomato":1.00,
	"Bok Choy":3.28,
	"Fuji Apple":5.49,
	"Red Delicious Apple":5.05,
	"Granny Apple":5.49,
	"Banana":1.52,
	"Vine Tomato":4.68,
	"Fresh Plum Tomato":5.49,
	"Braeburn Apple":5.00,
	"Nectarine":2.27,
	"Peach":6.59,
	"Cabbage":1.96,
	"Napa Cabbage":3.28,
	"Avocado":1.69,
	"Grapefruit Pink":1.99,
	"Kale":3.49,
	"Romaine Lettuce":3.69,
	"Mango":1.69,
	"Parsley":1.99,
	"Cilantro":2.99,
	"Grapefruit White":2.00
}

# grocery list
GROCERY_LIST = {}

def reset_grocerylist():
	global GROCERY_LIST
	GROCERY_LIST = {}


# global variables
WEIGHT = 0


# receipt total
def recalculate_subtotal():
	total = 0.0
	for produce, weight in GROCERY_LIST.items():
		total += weight * PRICE_DATABASE[produce]

	return total


# current Toronto time
UTC_OFFSET = 4		# 4 for UTC -4

def reset_time():
	utc_datetime = datetime.datetime.utcnow()
	result_datetime = utc_datetime - datetime.timedelta(hours=UTC_OFFSET)
	return result_datetime.strftime("%Y-%m-%d %H:%M")


## Website Routes -----------------------------------------------------------------------------

# homepage
@app.route('/')
def welcome():
	return render_template('layout.html', receipt=GROCERY_LIST, time=reset_time(), db=PRICE_DATABASE, total=recalculate_subtotal())


# upload page
@app.route('/uploads', methods=['POST'])
def upload():
	"""[summary]
	
	Defines the functionality of the upload function
	Using the library flask_uploads, this function uplaods an external picture into a local folder and renames it to test.jpg
	The image is then displayed on the webapp
	Due to HTML5 functionality, this part of the webapp can utilize a mobile phone's camera
	Will only accept still images in jpg file format

	Returns:
		A page redirect to the welcome function, which is basically a refresh of the home page.
	"""

	if request.method == 'POST' and 'photo' in request.files:
		if os.path.isfile("static/image/test.jpg"):
			os.remove("static/image/test.jpg")
		image_file = photos.save(request.files['photo'], name="test.jpg")
		flash('Uploaded')
		return redirect(url_for('welcome'))
	flash('Nothing Uploaded')
	return redirect(url_for('welcome'))


# after clicking the analyze button
@app.route('/aferscan', methods=['GET'])
def analyze_request():
	"""[summary]
	
	Generates a random weight for the analyzed produce between 0.1 to 3

	Then it sends the image to Watson's VR to be analyzed with parameters:
		1) Minimum threshold: 0.6
		2) Classifiers to use: specified in classifier_ids above in Watson configurations

	After Watson returns a result, the code gets the top 3 results. 
	If there are less than 3, it just gets all of them.
	If there are no results, the result will be "class:Unidentified"

	There contains a TEST portion in this code for GUI testing. Uncomment for testing purposes, otherwise, please ignore

	Returns:
		Redirects to the page afterscan.html, where it displays the results of the analysis
	"""

	# start_time = timeit.default_timer()			# used for timing performance during testing

	global WEIGHT
	WEIGHT = uniform(0.1,3)

	with open('static/image/test.jpg', 'rb') as image_file:
		classes = vr.classify(image_file, parameters=json.dumps({
			'classifier_ids':[classifier_id],
			'threshold':0.6
			}))
	# print(json.dumps(classes, indent=2))
	results = classes['images'][0]['classifiers'][0]['classes']

	# get top 3 results
	top_results = []								# list to hold the top 3 results
	max_score = {"class":"","score":0}				# temp dictionary to hold the top result while searching
	max_index = 0									# variable used to identify the location of the temp top result

# Testing Code START ##############################################################################################################################################
# uncomment the lines below for testing purposes
	
	# results = []

	# results.append({"class":"Mango", "score":0.99})
	# results.append({"class":"Bok Choy", "score":0.8})
	# results.append({"class":"Peach", "score":0.7})
	# results.append({"class":"Banana", "score":0.9})

	# results.append({"class":"Unidentified", "score":0})

# Testing Code END ##############################################################################################################################################

	def sort_key(results):
		"""
		An explicit lambda function for the sorted function on line 201
		"""
		return results["score"]	

	if len(results) < 4:							# if there are less than 4 results, no need to find top 3
		max_fruit = len(results)
		if max_fruit == 0:							# if there are no results
			top_results.append({"class":"Unidentified", "score":0})
		else:										# if there are 1 - 3 results, just sort them
			top_results = sorted(results, key=sort_key, reverse=True)

	else:											# if there are at least 4 results
		max_fruit = 3
		while len(top_results) < max_fruit:
			count = 0
			for i in results:
				if i["score"] > max_score["score"]:
					max_score = i
					max_index = count
				count += 1
			top_results.append(max_score)
			max_score = {"class":"","score":0}		# resets the temp variable
			del results[max_index]

	# print(json.dumps(top_results, indent=2))

	# stop_time = timeit.default_timer()
	# print(stop_time - start_time)

	return render_template('afterscan.html', data=top_results, weight=WEIGHT, receipt=GROCERY_LIST, time=reset_time(), db=PRICE_DATABASE, total=recalculate_subtotal())


@app.route('/add_to_list', methods=['POST'])
def add():
	"""[summary]
		
	The add button functionality. 
	After clicking the add button, the chosen produce will be added to GROCERY_LIST and the grocery receipt will update its contents

	Returns:
		Redirects to home page
	"""
	global GROCERY_LIST
	produce = request.values.get("chosen")
	# print("produce: ", produce)
	GROCERY_LIST[produce] = WEIGHT
	flash('Added')
	return render_template('layout.html', receipt=GROCERY_LIST, db=PRICE_DATABASE, time=reset_time(), total=recalculate_subtotal())


@app.route('/restart')
def reset():
	"""
		The erase grocery list button functionality

		Returns:
			Redirects to home page
	"""
	reset_grocerylist()
	flash('Receipt has been erased')
	return redirect(url_for('welcome'))
	


## Other Configurations --------------------------------------------------------------------------------
# These configurations were needed for HTML/CSS testing, but do not participate in the final app functionality

# to update the CSS so that cache won't memorize the previous CSS
@app.context_processor
def override_url_for():
	return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
	if endpoint == 'static':
		filename = values.get('filename', None)
		if filename:
			file_path = os.path.join(app.root_path, endpoint, filename)
			values['q'] = int(os.stat(file_path).st_mtime)
	return url_for(endpoint, **values)



## execute app locally on port 5000 --------------------------------------------------------------------
port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)