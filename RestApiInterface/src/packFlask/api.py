# -*- coding: utf-8 -*-

"""
IN this clase we define REST API actions. We define what url is needed and what actions we need to perform

"""

from json import dumps
from src.packORM import post_orm
from src.packORM import tables
from flask import Flask, request, make_response, Response, abort
from sqlalchemy.orm import class_mapper

__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


app = Flask(__name__)

@app.route('/add_action', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Ensure that we are sending Json format data
        if request.headers['content-type'] == 'application/json':
            data = request.json  # Request data in JSON formar if is bad flask makes a 400 response
            if data and 'location' in data: # todo we can send empty data? and data.get('location') is not none.....
                new_location = tables.Location(location=data.get('location', None))  # Creating new location
                orm = post_orm.PostgORM()
                # Need to control this part
                orm.insert_one(new_location)
                # Commit and close
                orm.commit()
                resp = make_response("Data stored in DB OK \n")
                return resp
            else:
                # Data is incorrect
                abort(500)
        else:
            # User submitted an unsupported Content-Type
            abort(400)
    else:
        orm = post_orm.PostgORM()
        # Return one user: This is an example test
        res = orm.query(tables.User)
        # todo we need to decide if we want to request all datasets or only one.
        serialized_labels = [serialize(label) for label in res]
        #res_json = dumps(serialized_labels)

        # Only one dataset
        #return jsonify(**serialized_labels[0])

        # multiple datasets(not recommended)
        return Response(dumps(serialized_labels), mimetype='application/json')

@app.errorhandler(400)
def not_found(error):
    resp = make_response("Your content type or data is not in JSON format\n", 400)
    return resp

@app.errorhandler(500)
def data_sent_error(error):
    resp = make_response("Data entered is invalid, please check your JSON headers\n", 500)
    return resp


def serialize(model):
    """Transforms a model into a dictionary which can be dumped to JSON."""
    # first we get the names of all the columns on your model
    columns = [c.key for c in class_mapper(model.__class__).columns]
    # then we return their values in a dict
    return dict((c, getattr(model, c)) for c in columns)


# todo change the location of the main execution file
if __name__ == '__main__':
    app.run(debug=True)


"""

curl -X POST -d @filename.txt http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/add_action --header "Content-Type:application/json"

"""


