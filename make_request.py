import requests
import json

with open("input_data.json") as json_file:
    data = json.loads(json_file.read())
#response = requests.get('http://echkin.pythonanywhere.com/', json=data)
response = requests.get('http://localhost:5000/', json=data)
print(response.content)
# DOES NOT WORK LOCALLY -> USE NEOS (cplex)