# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
# Deploy with `firebase deploy`
from firebase_functions import firestore_fn, https_fn#, logger <-- logger ins't in release version of firebase_functions yet
from flask import Response, json, redirect
import urllib.parse
import requests
from datetime import datetime
from bs4 import BeautifulSoup


# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore, auth
import google.cloud.firestore
from os import getenv

import logging

logger = logging.getLogger('cloudfunctions.googleapis.com%2Fcloud-functions')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

app = initialize_app()

#############################
#############################
#                           #
# Strava Webhook            #
#                           #
#############################
#############################

@https_fn.on_request(
        secrets=["Strava-Verify-Token", "Strava-Auth-Password"],
        region="europe-west2")
def callback(req: https_fn.Request) -> https_fn.Response:
    reqauth = req.authorization
    if reqauth is None or reqauth.username != "strava" or reqauth.password != getenv("Strava-Auth-Password"):
        return https_fn.Response("Unauthorized Access", status=401)
    if req.method == "GET" and req.args.get("hub.mode") == "subscribe" and req.args.get("hub.challenge"):
        return hub_challenge(req)
    elif req.method == "POST":
        data=req.json
        if "object_type" not in data:
            return https_fn.Response("Unexpected Request. (Object Type not present)", status=400)
        if data["object_type"] == "activity":
            return activity(req)
        elif data["object_type"] == "athlete":
            return athlete(req)
        else:
            return https_fn.Response("Unexpected Request. (Unknown Object Type)", status=400)
    else:
        return https_fn.Response("Unexpected Request.", status=400)
    
def hub_challenge(req: https_fn.Request) -> https_fn.Response:
    hub_verify_token = req.args.get("hub.verify_token")
    if hub_verify_token != None and hub_verify_token == getenv("Strava-Verify-Token"):
        return Response(
            json.dumps({"hub.challenge": req.args.get("hub.challenge")}),
            status=200, mimetype="application/json")
    else:
        return https_fn.Response("Wrong verify token", status=400)
    
def activity(req: https_fn.Request) -> https_fn.Response:
    # store activity update in firestore
    firestore_client: google.cloud.firestore.Client = firestore.client()
    data=req.json
    data["update_received_date"] = firestore.SERVER_TIMESTAMP
    data["update_status"] = "new"
    data["event_time"] = datetime.fromtimestamp(req.json["event_time"])
    firestore_client.collection("activity-updates").add(data)
    return https_fn.Response("Activity update received.", status=200)

def athlete(req: https_fn.Request) -> https_fn.Response:
    # store athlete update in firestore
    firestore_client: google.cloud.firestore.Client = firestore.client()
    data=req.json
    data["update_received_date"] = firestore.SERVER_TIMESTAMP
    data["update_status"] = "new"
    data["event_time"] = datetime.fromtimestamp(req.json["event_time"])
    firestore_client.collection("athlete-updates").add(data)
    return https_fn.Response("Athlete update received.", status=200)


#############################
#############################
#                           #
# Strava Auth               #
#                           #
#############################
#############################

@https_fn.on_request(
        secrets=["STRAVA_CLIENT_ID"],
        region="europe-west2")
def authorize_strava(req: https_fn.Request) -> https_fn.Response:
    params = {
        "client_id": getenv("STRAVA_CLIENT_ID"),
        "redirect_uri": "https://strava-ukc.web.app/api/verify_authorization",
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read"
    }
    url = "https://www.strava.com/oauth/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)

@https_fn.on_request(
        secrets=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET"],
        region="europe-west2")
def verify_authorization(request):
    code = request.args.get("code")
    if not code:
        return Response("Error: Missing code param", status=400)
    scope = request.args.get("scope")
    if "activity:read" not in scope or "read" not in scope:
        return Response("Sorry. You need to give Activity Read permission to get activities to upload public activities to UKC.", status=400)
        # TODO: upade this so users can give read all activities permission

    strava_request = requests.post(
        "https://www.strava.com/oauth/token",
        json={
            "client_id": getenv("STRAVA_CLIENT_ID"),
            "client_secret": getenv("STRAVA_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code"
        }
    )
    data = strava_request.json()

    ## update athlete in firestore
    updateAthleteInFirestore(data["athlete"])
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    expires_at = data["expires_at"]
    athleteID = data["athlete"]["id"]
    updateAthleteAuthInFirestore(access_token,refresh_token,expires_at,athleteID)

    # generate firebase login token
    firebase_token = auth.create_custom_token(str(athleteID))
    firebase_token_str = str(firebase_token)
    # TODO: could make this conversion better. Taking off first 2 chars, and last char.
    firebase_token_str = firebase_token_str[2:-1]

    #create redirect string to send back to front end
    params= {
        'token': firebase_token_str
    }
    front_end_url = "https://strava-ukc.web.app/completelogin?" + urllib.parse.urlencode(params)
    return redirect(front_end_url)

def updateAthleteInFirestore(athlete):
    db = firestore.client()
    athlete_ref = db.collection(u'users').document(str(athlete["id"]))
    athlete_ref.set({
        u'firstname': athlete["firstname"],
        u'lastname': athlete["lastname"],
        u'profile': athlete["profile"]
    }, merge=True)

def updateAthleteAuthInFirestore(access_token,refresh_token,expires_at,athlete_id):
    db = firestore.client()
    athlete_ref = db.collection(u'users').document(str(athlete_id))
    auth_ref = athlete_ref.collection(u'private').document(u'auth')
    auth_ref.set({
        u'access_token': access_token,
        u'refresh_token': refresh_token,
        u'expires_at': expires_at,
    })


#############################
#############################
#                           #
# Testing                   #
#                           #
#############################
#############################

@https_fn.on_request(region="europe-north1")
def addmessage(req: https_fn.Request) -> https_fn.Response:
    """Take the text parameter passed to this HTTP endpoint and insert it into
    a new document in the messages collection."""
    # Grab the text parameter.
    original = req.args.get("text")
    if original is None:
        return https_fn.Response("No text parameter provided", status=400)

    firestore_client: google.cloud.firestore.Client = firestore.client()

    # Push the new message into Cloud Firestore using the Firebase Admin SDK.
    _, doc_ref = firestore_client.collection("messages").add({"original": original})

    # Send back a message that we've successfully written the message
    return https_fn.Response(f"Message with ID {doc_ref.id} added.")

###############################
###############################
#                             #
# Trigger on Activity Updates #
#                             #
###############################
###############################

@firestore_fn.on_document_created(
        document="activity-updates/{pushId}",
        secrets=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET"],
        region="europe-west2")
def activity_trigger(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    # Get the value of "original" if it exists.
    if event.data is None:
        return
    if event.data.get("update_status") != "new":
        return
    # set update_status to processing
    firestore_client: google.cloud.firestore.Client = firestore.client()
    update_ref = firestore_client.collection("activity-updates").document(event.document.split("/")[-1])
    update_ref.set({
        u'update_status': 'processing',
    }, merge=True)

    # Check if auto upload is enabled for the user
    uid = event.data.get("owner_id")
    user_ref = firestore_client.collection(u'users').document(str(uid))
    user_doc = user_ref.get()
    if not user_doc.exists:
        update_ref.delete()
        return
    user_data = user_doc.to_dict()
    if not "auto_upload" in user_data or not user_doc.get("auto_upload"):
        update_ref.delete()
        return
    visibility = user_data.get("auto_upload_visibility", "everyone")
    route = user_data.get("gpx_upload", False)
    
    # Check if aspect_type is "create" "update" or "delete"
    if event.data.get("aspect_type") == "create" or event.data.get("aspect_type") == "update":
        status, error = update_entry(firestore_client, event.data, uid, visibility, route)
    elif event.data.get("aspect_type") == "delete":
        status, error = delete_entry(firestore_client, event.data, uid)
    else:
        status = 'error'
        error = 'aspect_type not create, update or delete'

    update_ref.set({
        u'update_status': status,
        u'update_message': error,
    }, merge=True)


def create_entry(firestore_client, data, uid, visibility, route):
    return upload_entry_to_UKC(firestore_client, data, uid, visibility, route)

def update_entry(firestore_client, data, uid, visibility, route):
    activity_id = data.get("object_id", data.get("id"))
    activity_ref = firestore_client.collection(u'users').document(str(uid)).collection(u'activities').document(str(activity_id))
    activity_doc = activity_ref.get()
    if not activity_doc.exists:
        return create_entry(firestore_client, data, uid, visibility, route)
    activity_data = activity_doc.to_dict()
    UKC_id = activity_data.get("UKC_id")
    return upload_entry_to_UKC(firestore_client, data, uid, visibility, route, UKC_id)

def delete_entry(firestore_client, data, uid):
    # Check if activity is already in firestore
    activity_id = data.get("object_id")
    activity_ref = firestore_client.collection(u'users').document(str(uid)).collection(u'activities').document(str(activity_id))
    activity_doc = activity_ref.get()
    if not activity_doc.exists:
        return 'success', 'We have not uploaded this activity to UKC before'
    activity_data = activity_doc.to_dict()
    UKC_id = activity_data.get("UKC_id")
    return upload_entry_to_UKC(firestore_client, data, uid, UKC_id=UKC_id, delete=True)

def should_upload_to_UKC(auto_upload_visibility, activity_visibility):
    # activity visibility can be 'everyone', 'followers_only', 'only_me'
    # if auto_upload_visibility is 'everyone' only upload if activity_visibility is 'everyone'
    # if auto_upload_visibility is 'followers_only' only upload if activity_visibility is 'everyone' or 'followers_only'
    # if auto_upload_visibility is 'only_me' upload all activities
    if auto_upload_visibility == 'only_me':
        return True
    if auto_upload_visibility == 'followers_only' and activity_visibility != 'only_me':
        return True
    if activity_visibility == 'everyone':
        return True
    return False

    
def upload_entry_to_UKC(firestore_client, data, uid, visibility='everyone', route=False, UKC_id=None, delete=False):
    form_data = {}
    if not delete:
        form_data, activity_visibility = get_form_data_for_activity(firestore_client, data, uid, route)
        if form_data is None or not should_upload_to_UKC(visibility, activity_visibility):
            delete = True
        elif UKC_id:
            form_data['id'] = UKC_id
            form_data['update'] = 'Update entry'
    if delete:
        if UKC_id is None:
            return 'success', 'We have not uploaded this activity to UKC before, no changes made.'
        form_data = {
            'id': UKC_id,
            'delete': 'Delete from diary',
        }
    # print('form_data', form_data)
    # first try with existing auth code
    auth_code = get_UKC_auth_code(firestore_client, uid)
    response = send_entry_to_UKC(auth_code, form_data)
    error = ''
    if response.status_code == 200:
        # Extract the page title
        page_title = get_page_title(response)

        # Check if auth didn't work
        if 'Login' in page_title:
            logger.info("Login required. Obtaining a new auth code.")

            # Obtain a new auth code
            auth_code = get_new_UKC_auth_code(firestore_client, uid)

            logger.info("New auth code saved. Reattempting activity submission.")

            # Retry activity submission with the new auth code
            response = send_entry_to_UKC(auth_code, form_data)

            # Check the response after retry
            if 'Login' in get_page_title(response):
                error = "Login failed a 2nd time."
                logger.error("Login failed a 2nd time. Error submitting activity.")
            elif response.status_code == 200:
                logger.info("Activity submitted successfully after retry.")
            else:
                error = f"Error submitting activity after retry. Status code: {response.status_code}"
                logger.error(f"Error submitting activity after retry. Status code: {response.status_code}")
                logger.error(response.text)
        else:
            logger.info("Activity submitted successfully.")
    else:
        error = f"Error submitting activity. Status code: {response.status_code}"
        logger.error(f"Error submitting activity. Status code: {response.status_code}")
        logger.error(response.text)
    if error != '':
        return 'error', error
    # analyse response
    analysis = analyse_upload_response(response)
    if analysis['status'] == 'success' and not UKC_id:
        UKC_id = analysis['id']
    if analysis['status'] == 'error':
        return 'error', analysis['error']
    if UKC_id:
        activity_id = data.get("object_id", data.get("id"))
        activity_ref = firestore_client.collection(u'users').document(str(uid)).collection(u'activities').document(str(activity_id))
        if delete:
            activity_ref.delete()
            return 'success', 'Activity deleted from UKC'
        else:
            activity_ref.set({
                u'UKC_id': UKC_id,
            }, merge=True)
        return 'success', 'Activity updated in UKC'
    else:
        return 'error', 'No UKC_id returned'

def get_page_title(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    page_title = soup.title.string if soup.title else 'No title found'
    return page_title

def analyse_upload_response(response):
    # ID is within <a href="adddiary.php?id=726080">Edit entry</a>
    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, 'html.parser')
    for link in soup.find_all('a'):
        if 'Edit entry' in link.text:
            return {'status':'success','id':link['href'].split('=')[1]}
    # check if entry isn't in this user's diary ("that entry isn't in your diary")
    if 'that entry isn\'t in your diary' in response.text:
        return {'status':'error','error':'Entry not in this user\'s diary'}
    # search for text within a div with class alert-danger
    for div in soup.find_all('div', class_='alert-danger'):
        return {'status':'error','error':div.text.strip()}
    # check if entry was deleted "Deleted that entry from your diary"
    if 'Deleted that entry from your diary' in response.text:
        return {'status':'success'}
    # check if entry was updated "Updated existing entry in your exercise diary"
    if 'Updated existing entry in your exercise diary' in response.text:
        return {'status':'success'}
    return {'status':'error','error':'Unknown error'}

def get_UKC_auth_code(firestore_client, uid):
    # Check if the auth code file exists
    athlete_ref = firestore_client.collection(u'users').document(str(uid))
    auth_ref = athlete_ref.collection(u'private').document(u'UKC_auth')
    auth = auth_ref.get().to_dict()
    if auth.get("auth_code", None) is not None:
        # Read the most recent auth code from the file
        auth_code = auth["auth_code"]
    else:
        # If the file doesn't exist, obtain a new auth code
        auth_code = get_new_UKC_auth_code(firestore_client, uid, auth["username"], auth["password"])
    return auth_code

def get_new_UKC_auth_code(firestore_client, uid, username=None, password=None):
    athlete_ref = firestore_client.collection(u'users').document(str(uid))
    auth_ref = athlete_ref.collection(u'private').document(u'UKC_auth')
    if username is None or password is None:
        # get username and password from firestore
        auth = auth_ref.get().to_dict()
        username = auth["username"]
        password = auth["password"]

    # Specify the login endpoint
    login_url = 'https://www.ukclimbing.com/user/'

    # Form data for login
    login_data = {
        'ref': '/',
        'email': username,
        'password': password,
        'login': '1',
    }

    # Create a session object
    session = requests.Session()

    # set referrer poicy to origin-when-cross-origin
    session.headers.update({'Referrer-Policy': 'origin-when-cross-origin'})
    session.cookies.update({'ukc_test': 'test'})
    session.cookies.update({'session_login': '1'})

    # Send a POST request to log in
    response = session.post(login_url, data=login_data, allow_redirects=True)

    wrong_password_text = 'The password or username/email you entered is invalid'
    if wrong_password_text in response.text:
        logger.warning("Wrong password entered.")
        # throw exception
        auth_ref.delete()
        # update user doc to turn off auto upload and add error message of incorrect UKC password
        user_ref = firestore_client.collection(u'users').document(str(uid))
        user_ref.set({
            u'auto_upload': False,
            u'auto_upload_error': 'Incorrect UKC password',
        }, merge=True)
        raise Exception("Wrong password entered.")
    
    # Loop through cookies to find one that has ukcsid
    for cookie in session.cookies:
        if cookie.name == 'ukcsid':
            auth_ref.set({u'auth_code': cookie.value}, merge=True)
            return cookie.value
        
    # If no ukcsid cookie was found, return None
    logger.error("No ukcsid cookie found.")
    raise Exception("Login failed.")

def send_entry_to_UKC(auth_code, form_data):
    # Authentication cookie
    auth_cookie = {'ukcsid': auth_code}

    # Create a session object to persist cookies
    session = requests.Session()
    session.cookies.update(auth_cookie)

    # Send a POST request with the session
    url_submit = 'https://www.ukclimbing.com/logbook/adddiary.php'
    response = session.post(url_submit, data=form_data)
    # Save response html content to file
    # with open('submit_response.html', 'w') as file:
    #     file.write(response.text)

    return response

def get_form_data_for_activity(firestore_client, data, uid, route):
    # TODO: respect stats_visibility privacy settings
    activity_id = data.get("object_id", None)
    if activity_id is not None:
        activity = get_activity_from_strava(firestore_client, uid, activity_id)
    else:
        activity_id = data.get("id", None)
        activity = data
    if activity is None or activity_id is None:
        return None, None
    # print('activity', activity)
    entry_type = map_type(activity["sport_type"], activity["distance"])
    start_time = datetime.strptime(activity["start_date_local"], "%Y-%m-%dT%H:%M:%SZ")
    timeslot = get_timeslot(start_time)
    date = get_date(start_time)
    duration_hr, duration_min, duration_sec = get_duration(activity["elapsed_time"])
    form_data = {
        'name': activity["name"],
        'activity': entry_type["activity"],
        'subactivity': entry_type["subactivity"],
        'timeslot': timeslot,
        'date': date,
        'duration_hr': duration_hr,
        'duration_min': duration_min,
        'duration_sec': duration_sec,
        'distance': str(round(activity["distance"]/1000,4)), # Distance in km
        'km': '1', # km as unit
        'description': activity["description"],
        'extra[0]': '',
        'extra[1]': activity.get("average_heartrate",''), # Heart rate (average bmp)
        'extra[2]': '', # Body weight (kg)
        'extra[3]': '', # Body fat (%)
        'extra[4]': activity.get("calories",''), # Calories
        'extra[5]': activity.get("average_cadence",''), # Cadence (average per minute)
        'extra[6]': activity.get("gear",{"name":''})["name"], # Shoes
        'extra[7]': '', # Laps TODO: add laps
        'extra[8]': '', # Intensity (1-5) TODO: add intensity (perhaps suffer_score)
        'extra[9]': activity["total_elevation_gain"], # Elevation gain (meters)
        'extra[1040]': f'https://www.strava.com/activities/{activity_id}', # Link to activity
        'update': 'Add entry',
    }
    if route:
        form_data['kml'] = get_activity_kml(firestore_client, uid, activity_id)
    return form_data, activity["visibility"]

def map_type(strava_type, distance):
    # Strava types: AlpineSki, BackcountrySki, Badminton, Canoeing, Crossfit, EBikeRide, Elliptical, EMountainBikeRide, Golf, GravelRide, Handcycle, HighIntensityIntervalTraining, Hike, IceSkate, InlineSkate, Kayaking, Kitesurf, MountainBikeRide, NordicSki, Pickleball, Pilates, Racquetball, Ride, RockClimbing, RollerSki, Rowing, Run, Sail, Skateboard, Snowboard, Snowshoe, Soccer, Squash, StairStepper, StandUpPaddling, Surfing, Swim, TableTennis, Tennis, TrailRun, Velomobile, VirtualRide, VirtualRow, VirtualRun, Walk, WeightTraining, Wheelchair, Windsurf, Workout, Yoga
    UKC_mapping = {
        'Indoor climbing': {'activity': '1', 'subactivity': 0},
        'Indoor climbing - Bouldering': {'activity': '1', 'subactivity': 3},
        'Indoor climbing - Routes': {'activity': '1', 'subactivity': 4},
        'Outdoor climbing': {'activity': '2', 'subactivity': 0},
        'Road running': {'activity': '3', 'subactivity': 0},
        'Trail running': {'activity': '4', 'subactivity': 0},
        'Walking': {'activity': '5', 'subactivity': 0},
        'Road biking': {'activity': '6', 'subactivity': 0},
        'Mountain biking': {'activity': '7', 'subactivity': 0},
        'Swimming': {'activity': '8', 'subactivity': 0},
        'Rowing': {'activity': '9', 'subactivity': 0},
        'Weights': {'activity': '10', 'subactivity': 0},
        'Exercise class': {'activity': '11', 'subactivity': 0},
        'Pilates': {'activity': '11', 'subactivity': 1},
        'Yoga': {'activity': '11', 'subactivity': 2},
        'Stretching': {'activity': '12', 'subactivity': 0},
        'Notes': {'activity': '14', 'subactivity': 0},
    }
    Strava_to_UKC = {
        'Canoeing': 'Rowing',
        'EBikeRide': 'Road biking',
        'EMountainBikeRide': 'Mountain biking',
        'Golf': 'Walking',
        'GravelRide': 'Mountain biking',
        'Handcycle': 'Road biking',
        'Hike': 'Walking',
        'Kayaking': 'Rowing',
        'MountainBikeRide': 'Mountain biking',
        'Ride': 'Road biking',
        'Rowing': 'Rowing',
        'Run': 'Road running',
        'Swim': 'Swimming',
        'TrailRun': 'Trail running',
        'Velomobile': 'Road biking',
        'VirtualRide': 'Road biking',
        'VirtualRow': 'Rowing',
        'VirtualRun': 'Road running',
        'Walk': 'Walking',
        'Yoga': 'Yoga',
    }
    if strava_type in Strava_to_UKC:
        strava_type = Strava_to_UKC[strava_type]
        return UKC_mapping[strava_type]
    if strava_type == 'RockClimbing':
        if distance and distance > 0:
            return UKC_mapping['Outdoor climbing']
        else:
            return UKC_mapping['Indoor climbing']
    return UKC_mapping['Exercise class']

def get_timeslot(start_date_local):
    hr = start_date_local.hour
    if hr < 12:
        return 1
    elif hr < 13:
        return 2
    elif hr < 18:
        return 3
    else:
        return 4

def get_date(start_date_local):
    return start_date_local.strftime("%d/%m/%Y")

def get_duration(elapsed_time):
    duration_hr = int(elapsed_time / 3600)
    duration_min = int((elapsed_time % 3600) / 60)
    duration_sec = int((elapsed_time % 3600) % 60)
    return duration_hr, duration_min, duration_sec

###############################
#                             #
# Strava Activity Getter      #
#                             #
###############################
    
def get_activity_from_strava(firestore_client, athleteID, activityID):
    #get access_token
    access_token = getAthleteAccessToken(firestore_client, athleteID)
    strava_request = requests.get(
        "https://www.strava.com/api/v3/activities/"+str(activityID),
        params={
            "Authorization": "Bearer",
            "access_token": access_token,
        }
    )
    # if status is 404, then activity is private, so do nothing
    if strava_request.status_code == 404:
        return
    strava_request.raise_for_status()
    return strava_request.json()
    
def getAthleteAccessToken(firestore_client, athleteID):
    #get the auth document
    athlete_ref = firestore_client.collection(u'users').document(str(athleteID))
    auth_ref = athlete_ref.collection(u'private').document(u'auth')
    auth = auth_ref.get().to_dict()
    # check if access token has expired
    currentTime = datetime.utcnow().timestamp()
    access_token = auth["access_token"]
    if auth["expires_at"] < currentTime:
        # if has expired, go get new access token with refresh token.
        access_token = getNewAccessToken(athleteID, auth["refresh_token"])
    return access_token

def getNewAccessToken(athleteID, refresh_token):
    # gets new access token from Strava oauth and save this in the database
    strava_request = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": getenv("STRAVA_CLIENT_ID"),
            "client_secret": getenv("STRAVA_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
    )
    access_token = strava_request.json()["access_token"]
    refresh_token = strava_request.json()["refresh_token"]
    expires_at = strava_request.json()["expires_at"]
    updateAthleteAuthInFirestore(access_token,refresh_token,expires_at,athleteID)
    return access_token

def get_activity_kml(firestore_client, athleteID, activityID):
    access_token = getAthleteAccessToken(firestore_client, athleteID)
    strava_request = requests.get(
        "https://www.strava.com/api/v3/activities/"+str(activityID)+"/streams?keys=distance,latlng,altitude&key_by_type=true",
        params={
            "Authorization": "Bearer",
            "access_token": access_token,
        }
    )
    data = strava_request.json()
    try:
        min_length = min(len(data['latlng']['data']), len(data['altitude']['data']), len(data['distance']['data']))
    except KeyError:
        return ''
    UKC_data = ''
    for i in range(min_length):
        UKC_data += f"{data['latlng']['data'][i][0]},{data['latlng']['data'][i][1]},{data['distance']['data'][i]},{data['altitude']['data'][i]}\n"
    return UKC_data

###############################
#                             #
# Set up UKC Auth             #
#                             #
###############################

@https_fn.on_call(region="europe-west2")
def set_up_UKC_auth(req: https_fn.CallableRequest) -> dict:
    if req.auth is None:
        # Throwing an HttpsError so that the client gets the error details.
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                                message="The function must be called while authenticated.")
    username = req.data.get("username")
    password = req.data.get("password")
    if username is None or password is None:
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                message="The function must be called with username and password arguments.")
    # test username and password
    firestore_client: google.cloud.firestore.Client = firestore.client()
    try:
        auth_code = get_new_UKC_auth_code(firestore_client, req.auth.uid, username, password)
    except Exception as e:
        if str(e) == 'Wrong password entered.':
            return {'success': False, 'error': 'Incorrect UKC username or password.'}
        else:
            raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                    message="Error setting up UKC auth.")
    # save username and password in firestore
    user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
    auth_ref = user_ref.collection(u'private').document(u'UKC_auth')
    auth_ref.set({
        u'username': username,
        u'password': password,
        u'auth_code': auth_code,
    })
    # turn on auto upload and store visibility
    user_ref.set({
        u'auto_upload': True,
        u'auto_upload_visibility': req.data.get("visibility", "everyone"),
        u'ukc_username': username,
        u'auto_upload_error': None,
    }, merge=True)

    # return success
    return {'success': True}


@https_fn.on_call(region="europe-west2")
def disable_auto_upload(req: https_fn.CallableRequest) -> dict:
    if req.auth is None:
        # Throwing an HttpsError so that the client gets the error details.
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                                message="The function must be called while authenticated.")
    # turn off auto upload
    firestore_client: google.cloud.firestore.Client = firestore.client()
    user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
    user_ref.set({
        u'auto_upload': False,
    }, merge=True)
    # delete auth stuff
    auth_ref = user_ref.collection(u'private').document(u'UKC_auth')
    auth_ref.delete()
    # return success
    return {'success': True}

@https_fn.on_call(region="europe-west2")
def enable_gpx_upload(req: https_fn.CallableRequest) -> dict:
    if req.auth is None:
        # Throwing an HttpsError so that the client gets the error details.
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                                message="The function must be called while authenticated.")
    firestore_client: google.cloud.firestore.Client = firestore.client()
    isSupporter = check_user_is_UKC_supporter(firestore_client, req.auth.uid)
    if not isSupporter:
        return {'success': False, 'error': 'You must be a UKC supporter to enable GPX upload.'}
    # turn on gpx upload
    user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
    user_ref.set({
        u'gpx_upload': True,
    }, merge=True)
    # return success
    return {'success': True}


@https_fn.on_call(region="europe-west2")
def disable_gpx_upload(req: https_fn.CallableRequest) -> dict:
    if req.auth is None:
        # Throwing an HttpsError so that the client gets the error details.
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                                message="The function must be called while authenticated.")
    # turn off gpx upload
    firestore_client: google.cloud.firestore.Client = firestore.client()
    user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
    user_ref.set({
        u'gpx_upload': False,
    }, merge=True)
    # return success
    return {'success': True}

def check_user_is_UKC_supporter(firestore_client, uid):
    auth_code = get_UKC_auth_code(firestore_client, uid)
    # with auth code, get user profile page (https://www.ukclimbing.com/user/profile.php) (and follow redirects)
    response = get_profile_page(auth_code)

    # to check if login worked, profile page should contain an <a> with href="/user/options.php?logout=1"
    # if login didn't work, get new auth code and try again
    if not check_login_for_profile_page(response):
        auth_code = get_new_UKC_auth_code(firestore_client, uid)
        response = get_profile_page(auth_code)
        if not check_login_for_profile_page(response):
            # if login still didn't work, throw an error
            raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                    message="Error checking if user is a UKC supporter.")

    # if login worked, check if user is a supporter
    # if supporter, page will contain an <a> with href="/user/supporter/"
    soup = BeautifulSoup(response.content, 'html.parser')
    for link in soup.find_all('a'):
        if 'href' in link.attrs and link['href'] == '/user/supporter/':
            return True
    return False

def get_profile_page(auth_code):
    auth_cookie = {'ukcsid': auth_code}
    # Create a session object to persist cookies
    session = requests.Session()
    session.cookies.update(auth_cookie)

    # Send a POST request with the session
    url = 'https://www.ukclimbing.com/user/profile.php'
    response = session.get(url)
    return response

def check_login_for_profile_page(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    for link in soup.find_all('a'):
        if 'href' in link.attrs and link['href'] == '/user/options.php?logout=1':
            return True
    return False

###############################
#                             #
# Trigger on Athlete          #
#                             #
###############################

firestore_fn.on_document_created(
        document="athlete-updates/{pushId}",
        secrets=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET"],
        region="europe-west2")
def athlete_trigger(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    # Get the value of "original" if it exists.
    if event.data is None:
        return
    if event.data.get("update_status") != "new":
        return
    # set update_status to processing
    firestore_client: google.cloud.firestore.Client = firestore.client()
    update_ref = firestore_client.collection("athlete-updates").document(event.document.split("/")[-1])
    update_ref.set({
        u'update_status': 'processing',
    }, merge=True)

    # Check if auto upload is enabled for the user
    uid = event.data.get("owner_id")
    user_ref = firestore_client.collection(u'users').document(str(uid))
    user_doc = user_ref.get()
    if not user_doc.exists:
        update_ref.delete()
        return
    
    # If authorized: "false" is in the event updates, then delete auth stuff
    if event.data.get("updates", {}).get("authorized", None) == "false":
        private_ref = user_ref.collection(u'private')
        private_ref.delete()
        user_ref.set({
            u'auto_upload': False,
            u'auto_upload_error': 'Strava authorization revoked',
        }, merge=True)
        update_ref.delete()
        return


###############################
#                             #
# Upload Previous Activities  #
#                             #
###############################

@https_fn.on_call(region="europe-west2")
def upload_previous_activities(req: https_fn.CallableRequest) -> dict:
    if req.auth is None:
        # Throwing an HttpsError so that the client gets the error details.
        raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.FAILED_PRECONDITION,
                                message="The function must be called while authenticated.")
    # check if auto upload is enabled for the user
    firestore_client: google.cloud.firestore.Client = firestore.client()
    user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
    user_doc = user_ref.get()
    if not user_doc.exists:
        return {'success': False, 'error': 'User not found'}
    user_data = user_doc.to_dict()
    # if not auto upload, check UKC username and password were provided and are correct
    if not "auto_upload" in user_data or not user_doc.get("auto_upload"):
        # if not, check UKC username and password were provided
        username = req.data.get("username")
        password = req.data.get("password")
        if username is None or password is None:
            raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INVALID_ARGUMENT,
                                    message="The function must be called with username and password arguments if Auto Upload is not enabled.")
        try:
            auth_code = get_new_UKC_auth_code(firestore_client, req.auth.uid, username, password)
        except Exception as e:
            if str(e) == 'Wrong password entered.':
                return {'success': False, 'error': 'Incorrect UKC username or password.'}
            else:
                raise https_fn.HttpsError(code=https_fn.FunctionsErrorCode.INTERNAL,
                                        message="Error setting up UKC auth.")
        # save username and password in firestore
        user_ref = firestore_client.collection(u'users').document(str(req.auth.uid))
        auth_ref = user_ref.collection(u'private').document(u'UKC_auth')
        auth_ref.set({
            u'username': username,
            u'password': password,
            u'auth_code': auth_code,
        })

    # TODO better before and after handling
    access_token = getAthleteAccessToken(firestore_client, req.auth.uid)
    visibility = user_data.get("auto_upload_visibility", "everyone")
    got_all_activities = False
    page = 0
    while not got_all_activities:
        page += 1
        strava_request = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            params={
                "Authorization": "Bearer",
                "access_token": access_token,
                "before": req.data.get("before", None),
                "after": req.data.get("after", None),
                "page": page,
                "per_page": 2, # max 200 TODO: increase this
            }
        )
        strava_request.raise_for_status()
        strava_activities = strava_request.json()
        if len(strava_activities) == 0:
            got_all_activities = True
        # for each activity in strava, update in UKC
        for strava_activity in strava_activities:
            status, error = update_entry(firestore_client, strava_activity, req.auth.uid, visibility, route=False)
            if status == 'error':
                return {'success': False, 'error': error}


    if not "auto_upload" in user_data or not user_doc.get("auto_upload"):
        # delete auth stuff
        auth_ref.delete()
    return {'success': True}