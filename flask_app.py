# A very simple Flask Hello World app for you to get started with...

from flask import Flask

app = Flask(__name__)

# @app.route('/')
# def hello_world():
#     return "Dans 5 min c'est 4"
# @app.route('/messages', methods = ['POST'])
# def api_message():

#     if request.headers['Content-Type'] == 'text/plain':
#         return "Text Message: " + request.data

#     elif request.headers['Content-Type'] == 'application/json':
#         return "JSON Message: " + json.dumps(request.json)

#     elif request.headers['Content-Type'] == 'application/octet-stream':
#         f = open('./binary', 'wb')
#         f.write(request.data)
#                 f.close()
#         return "Binary message written!"

#     else:
#         return "415 Unsupported Media Type ;)"

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from models.activity import Activity
import json
@app.route('/', methods = ['GET'])
def hello_world():
    data = request.json
    #data = json.loads(json_file.read())

    act = Activity(data)
    act.run()
    return "OK"
    # from models.activity import Activity
    # import json
    # data = request.json
    # #data = json.loads(json_file.read())
    # act = Activity(data)
    # act.run()
# app = Flask(__name__)
# api = Api(app)


# class W3go(Resource):
#     def get(self):
#         data = request.json
#         #data = json.loads(json_file.read())
#         act = Activity(data)
#         act.run()
#         # Return Output data
#         return data

# api.add_resource(W3go, '/')


# if __name__ == '__main__':
#     app.run(debug=True)