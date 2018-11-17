from flask import Flask, request, render_template, url_for, jsonify
from werkzeug.utils import secure_filename
import os
import http.client, urllib.request, urllib.parse, urllib.error, base64
import sqlite3
import uuid
import json
import urllib
import requests
from urllib import request as urlrequest
from PIL import Image
from io import BytesIO
import sendgrid
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/vinculum/server-side/vinculum/static/reuploads'
app.config['DATABASE'] = '/home/vinculum/server-side/vinculum/database1.db'


with open(app.root_path + '/rachana_config.json') as config_file:
    configuration = json.load(config_file)

    app.config['apikey'] = configuration['apikey']
    app.config['apiurl'] = configuration['apiurl']



@app.route('/')
def hello_world():
	return 'Hello world!'

@app.route('/email', methods=['POST'])
def send_email():
    sg = sendgrid.SendGridAPIClient(apikey='') #IMPORT SENDGRID API KEY FROM CONFIG
    print(request.form.get('name'))
    context = request.get_json(force=True)
    form_data = dict()
    for key, value in context.items():
        form_data[key] = value
    
    if "http" in form_data['searcher_image']:
        searcher_pic = (base64.b64encode(requests.get(form_data['searcher_image']).content)).decode('utf-8')
    else:
        searcher_pic = form_data['searcher_image']
    body_content = "A searcher would like to get in contact with {missing person's name}. Here is their info: \n Searcher name: " + form_data['searcher_name'] + "\n Searcher age: " + form_data['searcher_age'] + "\n Relation to missing person: " + form_data['searcher_relation'] + "\n Current location of searcher: " + form_data['searcher_location']+ "\n Contact info: " + form_data['searcher_contact'] + "\n Additional Info: " + form_data['searcher_info']
    body_content += "\n\n Details about missing person: \n Missing person name: " + form_data['missing_person_name'] + "\n Missing person age: " + form_data['missing_person_age'] +   "\n Nationality of missing person: " + form_data['searcher_location'] + "\n Source of missing person image: " + form_data['missing_person_image_source']
    body_content += "\n\n Details about source who uploaded info about missing person: \n Uploader name: " + form_data['missing_person_uploader_name'] + "\n Missing person relation to uploader: " + form_data['missing_person_uploader_relation'] +   "\n Contact info of image uploader: " + form_data['missing_person_contact']
    print(body_content)
    data = { 
            "personalizations": [ 
                { 
                "to": [ 
                    { "email": 'lrachana202@gmail.com', "name": 'Rachana' } ],
                    "subject": 'Vinculum: A match has been found'}],
                "content": [
                        {"type": 'text/plain',
                        "value": body_content}
                ],
                "attachments": [
                    {
                    "content": '',
                    "type": 'image/jpeg', 
                    "filename": 'Searcher'
                    },
                    {
                    "content": (base64.b64encode(requests.get(form_data['missing_person_image']).content)).decode('utf-8'),
                    "type": 'image/jpeg', 
                    "filename": 'Missing_Person_Image'
                    },
                    {
                    "content": '',
                    "type": 'image/jpeg', 
                    "filename": 'Photo_Submitted_By_Searcher'
                    }
                ],
                "from": { "email": 'lrachana@gmail.com', "name": 'Vinculum Webpage' }
            }

    print(personalizations)
    response = sg.client.mail.send.post(request_body=data)
    print('hello, email sent')
    return 'success',200

@app.route('/find', methods=['GET','POST'])
def find():
	if request.method == 'GET':
		context1 = 'teststring'
		return render_template('test.html', context = context1)

	elif request.method == 'POST':
		user = request.files['user']
		userfile = str(uuid.uuid4())
		#family = request.files['family']
		#familyfile = str(uuid.uuid4())
		db = sqlite3.connect(DATABASE)
		cursor = db.cursor()
		cursor.execute("INSERT INTO refugees (first_name, last_name, picturepath, age, gender, nationality, nickname) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(request.form.get('my_name'),request.form.get('my_last_name'), userfile,request.form.get('my_age'), request.form.get('my_sex'), request.form.get('my_nationality'), request.form.get('my_nickname')))
			
		#cursor.execute("INSERT INTO refugees (first_name, last_name, picturepath, age, gender, nationality, nickname) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(context['person_name'],context['person_last_name'], familyfile,context['person_age'], context['person_sex'], context['person_nationality'], context['person_nickname']))

		db.commit()	
		db.close()
		user.save(os.path.join(app.config['UPLOAD_FOLDER'], userfile))
		#family.save(os.path.join(app.config['UPLOAD_FOLDER'], familyfile))
		return 'success',200


@app.route('/match', methods=['GET'])
def match():
	url = '/reuploads/' + request.args.get('token')
	return get_matches(url)	


@app.route('/match/app', methods=['GET'])
def app_match():
    url = request.args.get('url')
    matches, confidence = get_matches(url)
    print(matches, confidence)
    matches = matches.decode('utf8')
    print(matches)
    matches = json.loads(matches)
    print(matches)
    url = matches['userData']
    userId = matches['personId']
    # start = str(data).find("name\":\"") + 7
    # end = str(data).find("\",\"userData")
    # url = str(data)[start:end]
    
    db = sqlite3.connect(app.config['DATABASE'])
    cursor = db.cursor()
    cursor.execute("SELECT * FROM refugees WHERE azure_response= '{}'".format(userId))
    returned = cursor.fetchone()
    print(returned)
    response = {'messages':[{'text': '%s%%' % int((confidence*100))},{'data':returned}, {'attachment':  {"type": "image","payload": {"url": 'http://23.101.170.100:5000/static/reuploads/'+returned[2]}}}]}
    print(response)
    return jsonify(response) 


@app.route('/upload', methods=['GET'])
def test_upload():
    return render_template('test_upload.html')


@app.route('/upload', methods=['POST'])
def web_upload():
    
    image = request.get_json()['image_string']
    imgdata = base64.b64decode(str(image))
    jpg = Image.open(BytesIO(imgdata)).convert("RGB")
    filename = uuid.uuid4().hex + '.jpg'
    jpg.save(os.path.join(app.config['UPLOAD_FOLDER'], filename), "jpeg")
    os.chmod(os.path.join(app.config['UPLOAD_FOLDER'], filename), 0o777)


    url = 'http://23.101.170.100:5000/static/reuploads/'+filename
    #url = 'http://localhost:5000/static/uploads/'+filename
    #url="https://media.licdn.com/dms/image/C5103AQGuXW3031fFdA/profile-displayphoto-shrink_800_800/0?e=1537401600&v=beta&t=HCjxOBSYrIdZ5_NZjHG_pxtVWutNERrZ4X0M4PT5V_w"
    print(url)
    #url = urllib.parse.quote_plus(url)
    #print(url)
    print("example urls")
    matches, confidence = get_matches_local(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    print(matches, confidence)
    matches = matches.decode('utf8')
    print(matches)
    matches = json.loads(matches)
    print(matches)
    url = matches['userData'] 
    personId = matches['personId']


    db = sqlite3.connect(app.config['DATABASE'])
    cursor = db.cursor()
    cursor.execute("SELECT * FROM refugees WHERE azure_response= '{}'".format(personId))

    response = cursor.fetchone()

    response = {'messages':[{'score': '%s%%' % int((confidence*100))},{'data': response }, {'attachment':  {"type": "image","payload": {"url": "http://23.101.170.100:5000/static/reuploads/"+response[2]}}}]}
    print(response)
    return jsonify(response) 
  



@app.route('/upload/app', methods=['GET'])
def enroll_user():
    url = request.args.get('url')
    fullname = request.args.get('fullname')
    age = request.args.get('age','0')
    gender = request.args.get('gender','')
    nationality = request.args.get('nationality','')
    uploader_name = request.args.get('uploader_name','')
    uploader_relation = request.args.get('uploader_relation', '')
    uploader_contact_info = request.args.get('uploader_contact_info', '')
    source = request.args.get('source')


    opener=urlrequest.build_opener()
    opener.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
    urlrequest.install_opener(opener)

    print('Submitted image: ' + url)
    filename = uuid.uuid4().hex + '.jpg'

    urlrequest.urlretrieve(url, os.path.join(app.config['UPLOAD_FOLDER'], filename))


    headers = {'Content-Type': 'application/json',
               'Ocp-Apim-Subscription-Key': subscription_key}
    params = urllib.parse.urlencode({})
    # Create Person
    conn = http.client.HTTPSConnection(app.config['apiurl'])
    body = "{'name': '%s', 'userData': '%s'}" % (fullname, url)
    conn.request("POST", "/face/v1.0/largepersongroups/2/persons?%s" % params, body, headers)
    response = conn.getresponse()
    data = response.read()
    person_id = eval(data)['personId']
    print(person_id)
    
    # Add Face
    body = "{'url': '%s'}" % url
    conn.request("POST", "/face/v1.0/largepersongroups/2/persons/%s/persistedfaces?%s" % (person_id, params), body, headers)
    response = conn.getresponse()
    data = response.read()
    print(data)

    # Re-train
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}
    conn.request("POST", "/face/v1.0/largepersongroups/2/train?%s" % params, "{}", headers)
    response = conn.getresponse()
    data = response.read()
    print(data)
    conn.close()

                                                                                     
    db = sqlite3.connect(app.config['DATABASE'])
    cursor = db.cursor()

    output = cursor.fetchall()
    cursor.execute("""INSERT INTO refugees (fullname, picturepath, age, gender, nationality, azure_response, uploader_name, uploader_relation, uploader_contact_info, source) values ('{}', '{}', {}, '{}', '{}', '{}', '{}' , '{}', '{}', '{}')""".format(fullname, filename, age, gender, nationality, person_id, uploader_name, uploader_relation, uploader_contact_info, source))

    db.commit()
    db.close()



    return 'success', 200

# CREATE A PERSON





subscription_key = app.config['apikey']



assert subscription_key           

def get_matches(url):
    ##### 1. Convert URL to a faceId
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
    })
    print(url)
    print(app.config['apiurl'])
    body = "{'url': '%s'}" % url
    try:
        conn = http.client.HTTPSConnection(app.config['apiurl'])
        conn.request("POST", "/face/v1.0/detect?%s" % params, body, headers)
        print(params)
        print(body)
        print(headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        face_id = eval(data)[0]['faceId']
        conn.close()
    except Exception as e:
        print(e)
    
    
    
    ##### 2. Get best matching personId from faceId
    params = urllib.parse.urlencode({
    })
    
    body = "{'faceIds': ['%s'], 'largePersonGroupId': '2', 'confidenceThreshold': '0.2'}" % face_id
    print(body)
    
    try:
        conn = http.client.HTTPSConnection(app.config['apiurl'])
        conn.request("POST", "/face/v1.0/identify?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        personId = eval(data)[0]['candidates'][0]['personId']
        confidence = eval(data)[0]['candidates'][0]['confidence']
        print(data)
        conn.close()
    except Exception as e:
        print("{}".format(str(e)))
    
    
    print(personId)
    
    
    ##### 3. Get name (which is filename) of personId
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
        'largePersonGroupId': '2',
        'personId': personId,
    })
    
    try:
        conn = http.client.HTTPSConnection(app.config['apiurl'])
        conn.request("GET", "/face/v1.0/largepersongroups/{largePersonGroupId}/persons/{personId}?%s" % params, "{}", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return data, confidence
    except Exception as e:
        print("[Errno {0}]".format(str(e)))

def get_matches_local(path):
    ##### 1. Convert URL to a faceId
    headers = {
        # Request headers
        'Content-Type': 'application/json',
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
    })
    print(path)
    print(app.config['apiurl'])
    data = open(path, 'rb').read()
    try:
        octet_params = {
                'Content-type':'application/octet-stream',
                'Ocp-Apim-Subscription-Key': subscription_key,
                }

        post_url = 'https://southcentralus.api.cognitive.microsoft.com/face/v1.0/detect?%s' % params
        response = requests.post(post_url, data=data, headers=octet_params)
        print(response.json())

        #conn = http.client.HTTPSConnection(app.config['apiurl'])
        #conn.request("POST", "/face/v1.0/detect?%s" % octet_params, headers, data)
        #print(params)
        #print(body)
        #print(headers)
        #response = conn.getresponse()
        #data = response.read()
        #print(data)
        face_id = response.json()[0]['faceId']
    except Exception as e:
        print('Exception: ' + e)
    
    
    
    ##### 2. Get best matching personId from faceId
    params = urllib.parse.urlencode({
    })
    
    body = "{'faceIds': ['%s'], 'largePersonGroupId': '2', 'confidenceThreshold': '0.2'}" % face_id
    print(body)
    
    try:
        conn = http.client.HTTPSConnection(app.config['apiurl'])
        conn.request("POST", "/face/v1.0/identify?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        personId = eval(data)[0]['candidates'][0]['personId']
        confidence = eval(data)[0]['candidates'][0]['confidence']
        print(data)
        conn.close()
    except Exception as e:
        print("{}".format(str(e)))
    
    
    print(personId)
    
    
    ##### 3. Get name (which is filename) of personId
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscription_key,
    }
    
    params = urllib.parse.urlencode({
        'largePersonGroupId': '2',
        'personId': personId,
    })
    
    try:
        conn = http.client.HTTPSConnection(app.config['apiurl'])
        conn.request("GET", "/face/v1.0/largepersongroups/{largePersonGroupId}/persons/{personId}?%s" % params, "{}", headers)
        response = conn.getresponse()
        data = response.read()
        print(data)
        conn.close()
        return data, confidence
    except Exception as e:
        print("[Errno {0}]".format(str(e)))   

if __name__ == '__main__':
	app.run(host='0.0.0.0')
