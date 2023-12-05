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
    return response

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
            response_after_retry = submit_activity(auth_code, form_data)

            # Check the response after retry
            if 'Login' in get_page_title(response_after_retry):
                print("Login failed a 2nd time. Error submitting activity.")
                raise Exception("Login failed a 2nd time. Error submitting activity.")
            elif response_after_retry.status_code == 200:
                print("Activity submitted successfully after retry.")
                print(f"Page Title: {get_page_title(response_after_retry)}")
            else:
                print(f"Error submitting activity after retry. Status code: {response_after_retry.status_code}")
                print(response_after_retry.text)
        else:
            print("Activity submitted successfully.")
    else:
        print(f"Error submitting activity. Status code: {response.status_code}")
        print(response.text)

def get_example_form_data():
    return {
        'name': 'Morning Run 15',
        'activity': '4',
        'subactivity': '0',
        'timeslot': '1',
        'date': '1/12/2023',
        'duration_hr': '',
        'duration_min': '31',
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
        'kml': get_kml(gpx_file),
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

def main():
    # Form post data extracted from the URL
    form_data = get_example_form_data()

    upload_activity_with_retry(form_data)

if __name__ == "__main__":
    main()