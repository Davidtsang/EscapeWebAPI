#!usr/bin/python
# -*- coding: utf-8 -*-

#Project game ranking NAME: cherry board;

from flask import Flask, jsonify, abort
from flask import make_response, url_for
from flask import request
import hashlib
import re
import time
import model
import base64
from functools import wraps


def md5(a_str):
    return hashlib.md5(a_str).hexdigest()


API_PRE_SHARED_KEY = md5(
    'The same came for a witness, to bear witness of the Light, that all men through him might believe.')

# https://iphonebestapp.com/msgtree.app/api/v1.0
# root  iphonebestapp.com/ssl/msgtree.app/

app = Flask(__name__)


@app.errorhandler(403)
def not_found(error):
    return make_response(jsonify({'error': 'Forbidden'}), 403)


@app.errorhandler(500)
def not_found(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


# some function

def check_list_in_dict(a_list, dest_dict):
    result = True
    for index_a_list in a_list:

        if not (index_a_list in dest_dict):
            result = False
            break

    return result


def token_check(a_token, timestamp, key):
    #app_key : base64(name:vesion)
    #base64.b64encode("msgtree:1.0") =>  'bXNndHJlZToxLjA='
    # try:
    #     a_token = base64.b64decode(a_token)
    # except:
    #     abort(403)

    vstring = str(timestamp) + ':' + key
    vhash = hashlib.md5(vstring).hexdigest()
    print 'is here'
    #timestamp < 12min
    now_time = time.time()
    if (now_time - int(float(timestamp)) ) > 7200:
        print "token over time!"
        return False

    print 'Right token shell be:', vhash
    if vhash == a_token:
        return True
    return False


def is_email_address_valid(email):
    """Validate the email address using a regex."""
    if not re.match("^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$", email):
        return False
    print 'email is ok'
    return True


def right_user_required(user_id ):

    rqs_user_id_str = request.args.get("user_id")

    vstring = str(user_id) + ':' + API_PRE_SHARED_KEY

    vhash = hashlib.md5(vstring).hexdigest()

    #print 'Right token shell be:', vhash
    if vhash != rqs_user_id_str:
        abort(400)


def auth_token_required(fn):
    @wraps(fn)
    def fn_wrap(*args, **kwargs):  # take any arguments

        #sid, session , user_id |
        if not request.args.get('auth_token') or not request.args.get('time_stamp'):
            abort(400)

        rqs_auth_token = request.args.get('auth_token', None)
        rqs_time_stamp = request.args.get('time_stamp').strip()

        rqs_ip = request.remote_addr

        vstring = str(rqs_time_stamp) + ':' + API_PRE_SHARED_KEY
        vhash = hashlib.md5(vstring).hexdigest()
        #print 'is here'

        now_time = time.time()
        if (now_time - int(float(rqs_time_stamp)) ) > 7200:
            print "token over time!"
            abort(400)


        if vhash != rqs_auth_token:
            abort(400)

        return fn(*args, **kwargs)  # pass any arguments to fn()

    return fn_wrap

#post, create a user safe : pre-shared key
@app.route('/api/v1.0/user', methods=['POST'])
@auth_token_required
def create_user():
    #get game id
    game_id = request.args.get("game_id")
    if not game_id:
        abort(400)
    user = model.User()
    user_id = user.create()
    return jsonify({'user_id': user_id})

#GET RANKING BEST
#GET api/v1.0/ranking/best?game_id=1
@app.route('/api/v1.0/ranking/best', methods=['GET'])
@auth_token_required
def get_ranking_best( ):
    #get game id
    game_id = request.args.get("game_id")
    if not game_id:
        abort(400)
    score = model.Ranking.find_best(game_id)
    return jsonify({'score': score})

# GET RANKING BEST
# GET api/v1.0/ranking/best?game_id=1
@app.route('/api/v1.0/user/<int:user_id>/beatrank', methods=['GET'])
@auth_token_required
def get_beatrank(user_id):
    #get game id
    game_id = request.args.get("game_id")
    user_score = request.args.get("score");
    if not game_id:
        abort(400)

    right_user_required(user_id)

    user = model.User(user_id)
    user_rank = user.my_rank(game_id, score_= user_score)
    if user_rank:
        user_beatrank = user.get_beatrank(user_rank)
        return jsonify({'beatrank': user_beatrank ,'user_rank':user_rank})
    else:
        return jsonify({'beatrank': 0,'user_rank':0 })


# update score etc
@app.route('/api/v1.0/user/<int:user_id>', methods=['PUT'])
@auth_token_required
def user_update(user_id):
    game_id = request.args.get("game_id")
    if not game_id:
        abort(400)

    right_user_required(user_id)

    user = model.User(user_id)
    rq = request
    if request.json.has_key("score") :
        #update notice
        user_score = request.json["score"]
        user.update_score(game_id,user_score)

    return jsonify({'success': 1 })



if __name__ == '__main__':
    app.run(debug=True)
