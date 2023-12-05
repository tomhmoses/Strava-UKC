import gpxpy
from gpxpy import gpx
import simplekml

def convert_gpx_to_kml(gpx_data):
    # Parse the GPX data
    gpx_parser = gpxpy.parse(gpx_data)

    # Create a KML object
    kml = simplekml.Kml()

    # Create a KML folder to hold the track
    folder = kml.newfolder(name='GPX Track')

    # Create a KML LineString for the track
    line = folder.newlinestring(name='GPX Track')

    list_of_distances = [0]
    prev_point = None

    # Extract track points from GPX and add them to the KML LineString
    for track in gpx_parser.tracks:
        for segment in track.segments:
            for point in segment.points:
                # UKC does latitude then logitude so we need to swap them
                line.coords.addcoordinates([(point.latitude, point.longitude,point.elevation)])
                if prev_point:
                    list_of_distances.append(point.distance_2d(prev_point)*0.001)
                prev_point = point

    # Save the KML data to a string
    kml_data = kml.kml()

    return kml_data, list_of_distances

def format_kml_for_UKC(kml_data, list_of_distances):
    # get string contents from within <coordinates> tags then replace spaces with newlines
    kml_data = kml_data.split('<coordinates>')[1].split('</coordinates>')[0]
    kml_lines = kml_data.split(' ')
    UKC_data = ''
    for i in range(len(kml_lines)):
        line_data = kml_lines[i].split(',')
        UKC_data += f'{line_data[0]},{line_data[1]},{list_of_distances[i]},{line_data[2]}\n'
    return UKC_data

def gpx_to_UKC_kml(gpx_data):
    kml_data, list_of_distances = convert_gpx_to_kml(gpx_data)
    return format_kml_for_UKC(kml_data, list_of_distances)

if __name__ == '__main__':
    # Example usage:
    # Assuming you have the GPX data in a variable named 'strava_gpx_data'
    strava_gpx_data = open('run.gpx', 'r').read()

    # Convert GPX to KML
    strava_kml_data, list_of_distances = convert_gpx_to_kml(strava_gpx_data)

    UKC_kml_data = format_kml_for_UKC(strava_kml_data, list_of_distances)

    # print number of lines in kml data
    print(f'Number of lines in kml data: {len(UKC_kml_data.splitlines())}')

    # Print first 10 lines of kml data
    print('First 10 lines of kml data:')
    for line in UKC_kml_data.splitlines()[:10]:
        print(line)
    
    # print last 5 lines
    print('Last 5 lines of kml data:')
    for line in UKC_kml_data.splitlines()[-5:]:
        print(line)

