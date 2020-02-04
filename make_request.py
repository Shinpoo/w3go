import requests
import json

with open("input_data.json") as json_file:
    data = json.loads(json_file.read())

response = requests.post('http://echkin.pythonanywhere.com/w3go/', json=data)
print(response.content)
response = requests.get('http://echkin.pythonanywhere.com/w3go/', json=data)
print(response.content)

#response = requests.get('http://localhost:5000/', json=data)
# DOES NOT WORK LOCALLY -> USE NEOS (cplex)