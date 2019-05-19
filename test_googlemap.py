import googlemaps
import pprint


API_key = "AIzaSyA97vDwjq2Lg4i6IqDDSWpcOV2GslKnjmE" # Don't forget to refresh key
gmaps = googlemaps.Client(key=API_key)
origins = (-10,-37)
destination = (-10.9401,-37.058729)

result = gmaps.distance_matrix(origins, destination, mode='walking')
pprint.pprint(result)