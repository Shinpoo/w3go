import googlemaps
import pprint


API_key = "AIzaSyBAGJ7YHgSD45b3OM-0UNzHLvKOOZ4E6Tg" # Don't forget to refresh key
gmaps = googlemaps.Client(key=API_key)
# origins = (-10,-37)
# destination = (-10.9401,-37.058729)

# boucheries = gmaps.places_autocomplete_query(input_text= "boucherie gourmande dison")
# print(boucheries)
result = gmaps.place(place_id = "ChIJk1BHeoyLwEcRdan0B__nn2U")

print(result)
# result = gmaps.distance_matrix(origins, destination, mode='walking')
pprint.pprint(result)
