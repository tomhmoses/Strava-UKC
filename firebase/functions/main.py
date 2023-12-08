# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
# Deploy with `firebase deploy`
from firebase_functions import firestore_fn, https_fn
from flask import Response, json, redirect
import urllib.parse
import requests
from datetime import datetime

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore, auth
import google.cloud.firestore
from os import getenv

app = initialize_app()

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
    firestore_client.collection("activity-updates").add(data)
    return https_fn.Response("Activity update received.", status=200)

    
def athlete(req: https_fn.Request) -> https_fn.Response:
    # store athlete update in firestore
    firestore_client: google.cloud.firestore.Client = firestore.client()
    data=req.json
    data["update_received_date"] = firestore.SERVER_TIMESTAMP
    data["update_status"] = "new"
    firestore_client.collection("athlete-updates").add(data)
    return https_fn.Response("Athlete update received.", status=200)

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

@https_fn.on_request(
        secrets=["STRAVA_CLIENT_ID"],
        region="europe-west2")
def authorize_strava(req: https_fn.Request) -> https_fn.Response:
    params = {
        "client_id": getenv("STRAVA_CLIENT_ID"),
        "redirect_uri": "https://strava-ukc.web.app/api/verify_authorization",
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all"
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
    if "activity:read_all" not in scope or "read" not in scope:
        return Response("Sorry. You need to give Activity Read All permission to get activities to upload to UKC.", status=400)
        # TODO: upade this so users can give just read permission so only public activities are uploaded

    # code here is an authorization code
    # what this url will look like
    #http://localhost/?state=&code=270cad31929190f0f41608aa3a5e16c89629d43a&scope=read,activity:read_all
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
    #could make this conversion better. Taking off first 2 chars, and last char.
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

@firestore_fn.on_document_created(
        document="activity-updates/{pushId}",
        secrets=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET"],
        region="europe-west2")
def activity_trigger(event: firestore_fn.Event[firestore_fn.DocumentSnapshot | None]) -> None:
    # Get the value of "original" if it exists.
    if event.data is None:
        return
    
    # Check if auto upload is enabled for the user
    uid = event.data.get("owner_id")
    firestore_client: google.cloud.firestore.Client = firestore.client()
    user_ref = firestore_client.collection(u'users').document(str(uid))
    user_doc = user_ref.get()
    if not user_doc.exists:
        print("user does not exist, deleting update")
        firestore_client.collection("activity-updates").document(event.document.split("/")[-1]).delete()
        return
    user_data = user_doc.to_dict()
    if not "auto_upload" in user_data or not user_doc.get("auto_upload"):
        print("auto upload not enabled, deleting update")
        firestore_client.collection("activity-updates").document(event.document.split("/")[-1]).delete()
        return
    
    # Check if aspect_type is "create" "update" or "delete"
    if event.data.get("aspect_type") == "create":
        create_entry(firestore_client, event.data, uid)
    elif event.data.get("aspect_type") == "update":
        update_entry(firestore_client, event.data, uid)
    elif event.data.get("aspect_type") == "delete":
        delete_entry(firestore_client, event.data, uid)

def create_entry(firestore_client, data, uid):
    print("create activity")
    upload_entry_to_UKC(firestore_client, data, uid)

def update_entry(firestore_client, data, uid):
    # Check if activity is already in firestore
    activity_id = data.get("object_id")
    activity_ref = firestore_client.collection(u'users').document(str(uid)).collection(u'activities').document(str(activity_id))
    activity_doc = activity_ref.get()
    if not activity_doc.exists:
        create_entry(firestore_client, data, uid)
        return
    activity_data = activity_doc.to_dict()
    UKC_id = activity_data.get("UKC_id")
    upload_entry_to_UKC(firestore_client, data, uid, UKC_id)

def delete_entry(firestore_client, data, uid):
    # Check if activity is already in firestore
    activity_id = data.get("object_id")
    activity_ref = firestore_client.collection(u'users').document(str(uid)).collection(u'activities').document(str(activity_id))
    activity_doc = activity_ref.get()
    if not activity_doc.exists:
        return
    activity_data = activity_doc.to_dict()
    UKC_id = activity_data.get("UKC_id")
    upload_entry_to_UKC(firestore_client, data, uid, UKC_id, delete=True)
    
def upload_entry_to_UKC(firestore_client, data, uid, UKC_id=None, delete=False):
    form_data = {}
    if delete:
        form_data = {
            'id': UKC_id,
            'delete': 'Delete from diary',
        }
    else:
        form_data = get_form_data_for_activity(firestore_client, data, uid)
        if UKC_id:
            form_data['id'] = UKC_id
            form_data['update'] = 'Update entry'
    print('form_data', form_data)

def get_form_data_for_activity(firestore_client, data, uid):
    activity_id = data.get("object_id")
    activity = get_activity_from_strava(firestore_client, uid, activity_id)
    # print('activity', activity)
    entry_type = map_type(activity["sport_type"], activity["distance"])
    start_time = datetime.strptime(activity["start_date_local"])
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
        'distance': activity["distance"]/1000, # Distance in km
        'km': '1', # km as unit
        'description': activity["description"],
        'extra[0]': '',
        'extra[1]': '150', # Heart rate (average bmp)
        'extra[2]': '', # Body weight (kg)
        'extra[3]': '', # Body fat (%)
        'extra[4]': activity["calories"], # Calories
        'extra[5]': activity["average_cadence"], # Cadence (average per minute)
        'extra[6]': activity["gear"]["name"], # Shoes
        'extra[7]': '', # Laps TODO: add laps
        'extra[8]': '', # Intensity (1-5)
        'extra[9]': activity["total_elevation_gain"], # Elevation gain (meters)
        'extra[1040]': f'https://www.strava.com/activities/{activity_id}', # Link to activity
        'update': 'Add entry',
    }
    return form_data

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