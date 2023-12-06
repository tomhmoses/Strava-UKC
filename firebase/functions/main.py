# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
# Deploy with `firebase deploy`
from firebase_functions import firestore_fn, https_fn
from flask import Response, json, redirect
import urllib.parse
import requests

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore, auth
import google.cloud.firestore
from os import getenv

app = initialize_app()

@https_fn.on_request(secrets=["Strava-Verify-Token", "Strava-Auth-Password"])
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

@https_fn.on_request()
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

@https_fn.on_request(secrets=["STRAVA_CLIENT_ID"])
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

@https_fn.on_request(secrets=["STRAVA_CLIENT_ID", "STRAVA_CLIENT_SECRET"])
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
        data={
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
    firebase_token = auth.create_custom_token(athleteID)
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