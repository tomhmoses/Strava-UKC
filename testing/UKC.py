import requests
from bs4 import BeautifulSoup
import os
from http.cookies import SimpleCookie
from gpx_to_kml import gpx_to_UKC_kml

# URL of the form submission endpoint
url_submit = 'https://www.ukclimbing.com/logbook/adddiary.php'
# URL of the login page
url_login = 'https://www.ukclimbing.com/logbook/cragadd.php'

# File to store the most recent auth code
auth_code_file = 'files/auth_code.txt'
# File to UKC user password
password_file = 'files/password.txt'
# KML example file
kml_file = 'files/example_kml.txt'
# GPX example file
gpx_file = 'run.gpx'

def example_kml():
    if os.path.exists(kml_file):
        # Read the most recent auth code from the file
        with open(kml_file, 'r') as file:
            return file.read().strip()
    else:
        raise Exception("Password file not found.")

# Credentials for logging in
def get_username():
    return 'tomhmoses'

def get_password():
    if os.path.exists(password_file):
        # Read the most recent auth code from the file
        with open(password_file, 'r') as file:
            return file.read().strip()
    else:
        raise Exception("Password file not found.")

def get_new_auth_code():
    # Specify the login endpoint
    login_url = 'https://www.ukclimbing.com/user/'

    # Form data for login
    login_data = {
        'ref': '/',
        'email': get_username(),
        'password': get_password(),
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
    # Save response html content to file
    # with open('login_response.html', 'w') as file:
    #     file.write(response.text)
    # print(f"Response status code: {response.status_code}")
    # # Parse the HTML content of the response
    # soup = BeautifulSoup(response.content, 'html.parser')
    # # Extract and print the page title
    # page_title = soup.title.string if soup.title else 'No title found'
    # print(f"Page Title: {page_title}")
    # # print(session cookies)
    # print(f"Session cookies: {session.cookies}")

    wrong_password_text = 'The password or username/email you entered is invalid'
    if wrong_password_text in response.text:
        print("Wrong password entered.")
        # throw exception
        raise Exception("Wrong password entered.")
    
    # Loop through cookies to find one that has ukcsid
    for cookie in session.cookies:
        if cookie.name == 'ukcsid':
            # print(f"Found ukcsid cookie: {cookie}")
            # print(f"Found ukcsid cookie: {cookie.value}")
            with open(auth_code_file, 'w') as file:
                file.write(cookie.value)
            return cookie.value
        
    # If no ukcsid cookie was found, return None
    print("No ukcsid cookie found.")
    raise Exception("Login failed.")

def submit_activity(auth_code, form_data):
    # Authentication cookie
    auth_cookie = {'ukcsid': auth_code}

    # Create a session object to persist cookies
    session = requests.Session()
    session.cookies.update(auth_cookie)

    # Send a POST request with the session
    response = session.post(url_submit, data=form_data)
    # Save response html content to file
    with open('submit_response.html', 'w') as file:
        file.write(response.text)

    return response

def get_activity_id(response):
    # this is within <a href="adddiary.php?id=726080">Edit entry</a>
    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, 'html.parser')
    # # Extract and print the page title
    # page_title = soup.title.string if soup.title else 'No title found'
    # print(f"Page Title: {page_title}")
    # print(soup.find_all('a'))
    for link in soup.find_all('a'):
        if 'Edit entry' in link.text:
            return link['href'].split('=')[1]
    return None

def get_auth_code():
    # Check if the auth code file exists
    if os.path.exists(auth_code_file):
        # Read the most recent auth code from the file
        with open(auth_code_file, 'r') as file:
            auth_code = file.read().strip()
    else:
        # If the file doesn't exist, obtain a new auth code
        auth_code = get_new_auth_code()
    return auth_code

def get_page_title(response):
    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract and print the page title
    page_title = soup.title.string if soup.title else 'No title found'
    return page_title

def upload_activity_with_retry(form_data):
    auth_code = get_auth_code()
    # Send the activity submission request
    response = submit_activity(auth_code, form_data)

    # Check the response
    if response.status_code == 200:
        # Extract and print the page title
        page_title = get_page_title(response)
        print(f"Page Title: {page_title}")

        # Check if auth didn't work
        if 'Login' in page_title:
            print("Login required. Obtaining a new auth code.")

            # Obtain a new auth code
            auth_code = get_new_auth_code()

            print("New auth code saved. Reattempting activity submission.")

            # Retry activity submission with the new auth code
            response = submit_activity(auth_code, form_data)

            # Check the response after retry
            if 'Login' in get_page_title(response):
                print("Login failed a 2nd time. Error submitting activity.")
                raise Exception("Login failed a 2nd time. Error submitting activity.")
            elif response.status_code == 200:
                print("Activity submitted successfully after retry.")
            else:
                print(f"Error submitting activity after retry. Status code: {response.status_code}")
                print(response.text)
        else:
            print("Activity submitted successfully.")
    else:
        print(f"Error submitting activity. Status code: {response.status_code}")
        print(response.text)
    with open('submit_response.html', 'w') as file:
                file.write(response.text)
    return analyse_upload_response(response)
    

def get_example_form_data():
    return {
        'name': 'Sample with Strava KML',
        'activity': '4',
        'subactivity': '0',
        'timeslot': '1',
        'date': '1/12/2023',
        'duration_hr': '',
        'duration_min': '3',
        'duration_sec': '',
        'distance': '5.11', # Distance in km
        'km': '1', # km as unit
        'description': 'Notes',
        'extra[0]': '',
        'extra[1]': '150', # Heart rate (average bmp)
        'extra[2]': '', # Body weight (kg)
        'extra[3]': '', # Body fat (%)
        'extra[4]': '376', # Calories
        'extra[5]': '', # Cadence (average per minute)
        'extra[6]': 'Scarpa Ribelle Run', # Shoes
        'extra[7]': '', # Laps
        'extra[8]': '', # Intensity (1-5)
        'extra[9]': '', # Elevation gain (meters)
        'extra[1040]': 'a', # Link to activity
        'update': 'Add entry',
        'kml': get_strava_kml(),
        # 'id': '', # Activity ID to update an existing activity
        # 'delete': 'Delete from diary', # Delete an existing activity, must be used with id
    }

def get_kml(gpx_file):
    # Read the GPX file
    gpx_data = open(gpx_file, 'r').read()
    # Convert GPX to KML
    kml_data = gpx_to_UKC_kml(gpx_data)
    return kml_data

def activity_type(name):
    mapping = {
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
    return mapping[name]

def delete_entry(activity_id):
    form_data = {
        'id': activity_id,
        'delete': 'Delete from diary',
    }
    print(upload_activity_with_retry(form_data))

def analyse_upload_response(response):
    # ID is within <a href="adddiary.php?id=726080">Edit entry</a>
    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, 'html.parser')
    for link in soup.find_all('a'):
        if 'Edit entry' in link.text:
            return {'status':'success','id':link['href'].split('=')[1]}
    # check if entry isn't in this user's dairy ("that entry isn't in your diary")
    if 'that entry isn\'t in your diary' in response.text:
        return {'status':'error','error':'Entry not in this user\'s diary'}
    # search for text within a div with class alert-danger
    for div in soup.find_all('div', class_='alert-danger'):
        return {'status':'error','error':div.text.strip()}
    # check if entry was deleted "Deleted that entry from your diary"
    if 'Deleted that entry from your diary' in response.text:
        return {'status':'success','id':None}
    return {'status':'error','error':'Unknown error'}

def get_UKC_auth_code(firestore_client, uid):
    return get_auth_code()

def get_new_UKC_auth_code(firestore_client, uid):
    return get_new_auth_code()

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
            return None

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



def get_activity_kml(activityID, access_token):
    # get   'https://www.strava.com/api/v3/activities/123/streams?keys=distance,latlng,altitude&key_by_type=true' \
    strava_request = requests.get(
        "https://www.strava.com/api/v3/activities/"+str(activityID)+"/streams?keys=distance,latlng,altitude&key_by_type=true",
        params={
            "Authorization": "Bearer",
            "access_token": access_token,
        }
    )
    data = strava_request.json()
    # print(data)
    print(len(data['latlng']['data']))
    print(len(data['altitude']['data']))
    print(len(data['distance']['data']))
    # min of three
    min_length = min(len(data['latlng']['data']), len(data['altitude']['data']), len(data['distance']['data']))
    UKC_data = ''
    for i in range(min_length):
        UKC_data += f"{data['latlng']['data'][i][0]},{data['latlng']['data'][i][1]},{data['distance']['data'][i]},{data['altitude']['data'][i]}\n"
    return UKC_data

def main():
    # Form post data extracted from the URL
    form_data = get_example_form_data()

    status = upload_activity_with_retry(form_data)
    print(f"Status: {status}")

def get_strava_kml():
    return get_activity_kml('10336313961', 'nope')

if __name__ == "__main__":
    main()
    # delete_entry('726263')
    # print(check_user_is_UKC_supporter(None, None))
    # activityKML = get_strava_kml()
    # print first 5
    # print(activityKML.splitlines()[:5])