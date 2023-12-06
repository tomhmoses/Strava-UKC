# The Cloud Functions for Firebase SDK to create Cloud Functions and set up triggers.
# Deploy with `firebase deploy`
from firebase_functions import firestore_fn, https_fn
from flask import Response, json

# The Firebase Admin SDK to access Cloud Firestore.
from firebase_admin import initialize_app, firestore
import google.cloud.firestore
from os import getenv

app = initialize_app()

@https_fn.on_request(secrets=["Strava-Verify-Token", "Strava-Auth-Password"])
def callback(req: https_fn.Request) -> https_fn.Response:
    auth = req.authorization
    if auth is None or auth.username != "strava" or auth.password != getenv("Strava-Auth-Password"):
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