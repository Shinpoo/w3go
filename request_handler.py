from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from models.activity import Activity
import json
app = Flask(__name__)
api = Api(app)


class W3go(Resource):
    def get(self):
        data = request.json
        #data = json.loads(json_file.read())
        act = Activity(data)
        act.run()
        # Return Output data
        return data

api.add_resource(W3go, '/')

if __name__ == '__main__':
    app.run(debug=True)