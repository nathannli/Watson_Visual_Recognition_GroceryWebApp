from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from watson_developer_cloud import VisualRecognitionV3
from flask_uploads import UploadSet, configure_uploads, IMAGES
from random import uniform
import json
import os
import time



"""[summary]

Returns:
	[type] -- [description]
"""


## Watson Configurations ---------------------------------------------------------------------------
vr = VisualRecognitionV3(
	"2016-05-20",
	api_key="843909e8ab8cbe39596df5ff4725d8a0fdb5e756"
)

classifier_id = "Ringo_IdentifAIer_408586032"


## Flask Configurations ------------------------------------------------------------------------------
app = Flask(__name__)               # creates an instance of Flask in app
app.config.from_object(__name__)    # load config from this file , flaskr.py
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


# global variables
WEIGHT = 0


## Website Routes -----------------------------------------------------------------------------

# homepage
@app.route('/')
def welcome():
	return render_template('layout.html', receipt=GROCERY_LIST, time=time.strftime("%Y-%m-%d %H:%M"))


# upload page
@app.route('/uploads', methods=['POST'])
def upload():
	"""[summary]
	
	Returns:
		[type] -- [description]
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
	
	Returns:
		[type] -- [description]
	"""

	global WEIGHT
	WEIGHT = uniform(0.5,3)

	with open('static/image/test.jpg', 'rb') as image_file:
		classes = vr.classify(image_file, parameters=json.dumps({
			'classifier_ids':[classifier_id],
			'threshold':0.6
			}))
	print(json.dumps(classes, indent=2))
	results = classes['images'][0]['classifiers'][0]['classes']
	top_results = []
	max_score = {"class":"","score":0}
	max_index = 0


	if len(results) < 3:
		max_fruit = len(results)
	else:
		max_fruit = 3


	# if max_fruit == 0:
	# 	top_results.append({"class":"Unidentified"})
	# else:
	# 	while len(top_results) < max_fruit:
	# 		count = 0
	# 		for i in results:
	# 			if i["score"] > max_score["score"]:
	# 				max_score = i
	# 				max_index = count
	# 			count += 1
	# 		top_results.append(max_score)
	# 		max_score = {"class":"","score":0}
	# 		del results[max_index]


	top_results.append({"class":"Banana", "score":0.9})
	top_results.append({"class":"Bok Choy", "score":0.8})
	top_results.append({"class":"Peach", "score":0.7})

	# top_results.append({"class":"Unidentified"})


	print(json.dumps(top_results, indent=2))
	return render_template('afterscan.html', data=top_results, weight=WEIGHT, receipt=GROCERY_LIST, time=time.strftime("%Y-%m-%d %H:%M"))

@app.route('/add_to_list', methods=['POST'])
def add():
	global GROCERY_LIST, WEIGHT
	produce = request.values.get("chosen")
	print("produce: ", produce)
	GROCERY_LIST[produce] = WEIGHT
	flash('Added')
	return render_template('layout.html', receipt=GROCERY_LIST, db=PRICE_DATABASE, time=time.strftime("%Y-%m-%d %H:%M"))

	


## Other Configurations --------------------------------------------------------------------------------

# to update the CSS so that cache wouldn't memorize the previous CSS
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