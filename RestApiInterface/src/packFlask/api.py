# -*- coding: utf-8 -*-

"""
IN this clase we define REST API actions. We define what url is needed and what actions we need to perform

"""

from packORM import post_orm, tables
from flask import Flask, request, make_response, jsonify, Response
from json import dumps
from sqlalchemy.orm import class_mapper

__author__ = 'Rubén Mulero'
__copyright__ = "foo"   # we need?¿


app = Flask(__name__)

@app.route('/add_action', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Ensure that we are sending Json format data
        if request.headers['content-type'] == 'application/json':
            # todo handle this with try cath block
            orm = post_orm.PostgORM()
            data = request.json  # Data in JSON format
            new_location = tables.Location(location=data['location']) # Creating new location
            res = orm.insert_one(new_location)
            # Only if ok
            orm.close()
            resp = make_response("Data stored in DB OK \n")
            orm.close()
            return resp
        else:
            # User submitted an unsupported Content-Type
            return Response(status=400)
    else:
        orm = post_orm.PostgORM()
        # Devolvemos un usuario
        res = orm.query(tables.User)
        serialized_labels = [serialize(label) for label in res]
        #res_json = dumps(serialized_labels)

        # Only one dataset
        #return jsonify(**serialized_labels[0])

        # multiple datasets(not recommended)
        return Response(dumps(serialized_labels), mimetype='application/json')


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

curl -X POST -d @filename.txt http://127.0.0.1:5000/ --header "Content-Type:application/json"

curl -X POST -d '{"name1":"Rodolfo","name2":"Pakorro"}' http://127.0.0.1:5000/ --header "Content-Type:application/json"

"""


