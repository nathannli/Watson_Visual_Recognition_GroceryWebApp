from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from watson_developer_cloud import VisualRecognitionV3
from flask_uploads import UploadSet, configure_uploads, IMAGES
import json
import os



vr = VisualRecognitionV3(
    "2016-05-20",
    api_key="843909e8ab8cbe39596df5ff4725d8a0fdb5e756"
)

classifier_id = "Ringo_IdentifAI_867145316"


def create_app():
    app = Flask(__name__)
    return app

app = create_app()
app.config.from_object(__name__)    # load config from this file , flaskr.py
photos = UploadSet("photos", IMAGES)

app.config.update(dict(
    SECRET_KEY='development key',
    UPLOADED_PHOTOS_DEST="static/image"
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
configure_uploads(app, photos)





@app.route('/')
def welcome():
    return render_template('layout.html')


@app.route('/', methods=['POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        if os.path.isfile("static/image/test.jpg"):
            os.remove("static/image/test.jpg")
        image_file = photos.save(request.files['photo'], name="test.jpg")
        flash('Uploaded')
        return redirect(url_for('welcome'))
    flash('Nothing Uploaded')
    return redirect(url_for('welcome'))


@app.route('/analyze', methods=['GET'])
def analyze_request():
    with open('static/image/test.jpg', 'rb') as image_file:
        classes = vr.classify(image_file, parameters=json.dumps({'classifier_ids':[classifier_id], 'threshold':0.6}))
    return render_template('analyze.html', data=classes['images'][0]['classifiers'][0]['classes'][0])



@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)




port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(port), debug=True)