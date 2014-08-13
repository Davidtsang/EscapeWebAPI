#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import os
import base64

import psycopg2
import psycopg2.extras

import platform


def get_env():

    env_dev_osname = 'Darwin-12.5.0-x86_64-i386-64bit'
    this_env = platform.platform()
    if(env_dev_osname.split('-')[0] == this_env.split('-')[0]):
        return 'env_dev'
    else:
        return 'env_production'

SESSION_EXPIRES = -1
SESSION_EXPIRES_TIMES = 3600

INBOX_THE_TYPE_PLANT_TEXT = 'PT'
INBOX_THE_TYPE_TEXT_BTN = 'TB'

FRIENDSHIP_STATUS_OK = 'OK'
FRIENDSHIP_STATUS_BAN = 'BA'



def create_table():
    conn = DB().get_conn()
    cur = conn.cursor()
    cur.execute("""
    
DROP TABLE IF EXISTS users ;
CREATE TABLE users(
   id SERIAL PRIMARY KEY NOT NULL,
   name  VARCHAR(150) ,
   email VARCHAR(150),
   avatar  BYTEA,
   password   VARCHAR(32),
   phone_number VARCHAR(24),
   fb_id VARCHAR (255),
   fb_name VARCHAR (255),
   fb_locale VARCHAR(4),
   fb_timezone INT,
   fb_email VARCHAR(150),
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);

DROP TABLE IF EXISTS  games ;
CREATE TABLE games(
   id SERIAL PRIMARY KEY NOT NULL,
   name VARCHAR(255) NOT NULL,
   version  VARCHAR (32) NOT NULL,
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);

DROP TABLE IF EXISTS  rankings ;
CREATE TABLE rankings(
   id SERIAL PRIMARY KEY     NOT NULL,
   score INT NOT NULL,
   user_id INT NOT NULL,
   game_id INT NOT NULL,
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);

DROP TABLE IF EXISTS  scores ;
CREATE TABLE scores(
   id SERIAL PRIMARY KEY     NOT NULL,
   score INT NOT NULL,
   user_id INT NOT NULL,
   game_id INT NOT NULL,
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);


    """)
    conn.commit()
    print "CREATE TABLE..."

def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class DB(object):
    conn = None

    @classmethod
    def get_conn(cls):
        if not cls.conn:
            cls.conn = DB().connect()
            print "Init conn"
        return cls.conn

    @classmethod
    def connect(cls):
        ''' INIT DB '''
        env = get_env()
        if env == 'env_dev':
            dbstr = "dbname=gameranking  user=user host=127.0.0.1  port=5432"
        else:
            dbstr = "dbname=gameranking  user=postgres password=z12345678 host=127.0.0.1  port=5432"

        conn = psycopg2.connect(dbstr)
        print "Opened database successfully"
        return conn


class CWModel:
    conn = DB().get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __init__(self, rid=None):
        self.fields = []

        self._table_name = self.__class__.__name__.lower() + 's'

        col_info = self._get_columns_info()

        for index_col_info in col_info:
            col_name = index_col_info[0]
            self.fields.append(col_name)

        # set attr table
        for field in self.fields:
            setattr(self, field, None)

            # gen find_%s method
            self.gen_find_by_methods(field)

        # get fields
        if rid:
            self.id = rid
            this_model_info = self.find_by_id(rid)
            # full attr
            for field in self.fields:
                setattr(self, field, this_model_info[field])

    def gen_find_by_methods(self, mname):


        def dn_find_by(col_val):
            sql = "SELECT * FROM %s WHERE %s" % (self._table_name, mname, )
            sql = sql + " = %s  LIMIT 1;"
            sql = self.cur.mogrify(sql, (col_val,))
            print sql
            self.cur.execute(sql)
            return self.cur.fetchone()

        dn_find_by.__name__ = "find_by_%s" % mname
        setattr(self, dn_find_by.__name__, dn_find_by)

    @classmethod
    def find_by(cls, where, table_name=None):
        if not table_name:
            table_name = cls.__name__.lower() + 's'
        sql = "SELECT * FROM %s WHERE %s ;" % (table_name, where, )
        # debug:
        print sql
        cls.cur.execute(sql)
        return cls.cur.fetchall()

    @classmethod
    def find_by_id(cls, a_id):
        table_name = cls.__name__.lower() + 's'
        sql = "SELECT * FROM %s WHERE id = %s LIMIT 1" % (table_name, a_id, )
        print sql
        cls.cur.execute(sql)
        return cls.cur.fetchone()

    def _get_columns_info(self):
        """ get col name feed fields """
        self.cur.execute("SELECT column_name FROM information_schema.columns \
        WHERE table_schema='public' AND table_name= %s ", (self._table_name,))
        return self.cur.fetchall()


    def update(self):

        cols = ",".join(self.fields)
        # print cols

        val_sign = ",".join(["%s"] * len(self.fields))
        sql_up = "UPDATE %s SET (%s) = (%s) WHERE id = %s" % \
                 (self._table_name, cols, val_sign, self.id)
        cols_value = []
        for field in self.fields:
            cols_value.append(getattr(self, field))

        sql = self.cur.mogrify(sql_up, (cols_value))

        print sql
        self.cur.execute(sql)
        self.conn.commit()

    def create(self):

        timestamp = int(time.time())

        self.updated_at = timestamp
        self.created_at = timestamp
        self.id = "DEFAULT"

        cols = ",".join(self.fields)

        val_sign = ",".join(["%s"] * len(self.fields))

        sql_up = "INSERT INTO %s (%s) VALUES (%s) RETURNING * " % \
                 (self._table_name, cols, val_sign)

        cols_value = []
        for field in self.fields:
            cols_value.append(getattr(self, field))

        sql = self.cur.mogrify(sql_up, (cols_value))
        sql = sql.replace("'DEFAULT'", "DEFAULT")

        print sql

        self.cur.execute(sql)

        self.conn.commit()

        return self.cur.fetchone()


class Ranking(CWModel):
    """ got_its table model
    """

    @classmethod
    def find_best(cls, game_id):
        sql = "game_id = %s ORDER BY score DESC LIMIT 1 " % (game_id )
        result = cls.find_by(sql)
        if result:
            return result[0]['score']
        return 0




class Score(CWModel):
    pass

class User(CWModel):
    # def __init__(self):
    # CWModel.__init__(self)

    @classmethod
    def is_unique(cls, email):

        # unique email;
        cls.cur.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email,));

        result = cls.cur.fetchone()
        if result != None:
            return result[0]
        else:
            return False



    def update_score(self, game_id, score_):

        #one game one user_id have one score
        where_str = "user_id = %s AND game_id = %s" % (self.id , game_id)

        score_id = Score.find_by(where_str)
        if score_id:
            score_id = score_id[0]['id']
            user_score = Score(score_id)
            user_score.score = score_
            user_score.update()
        else:
        #create
            score = Score()
            score.user_id = self.id
            score.game_id = game_id
            score.score = score_
            score.create()

        #try insert ranking
        where_str = "score = %s AND game_id = %s LIMIT 1" % (score_, game_id )
        has_score = Ranking.find_by(where=where_str)
        if not has_score:
            #CREAVTE NEW RANKING
            ranking = Ranking()
            ranking.score = score_
            ranking.user_id = self.id
            ranking.game_id = game_id
            ranking.create()


    def my_rank(self, game_id ,score_= None):
        #get self score
        if score_ == None:
            where_str = "user_id = %s LIMIT 1" % (self.id,)
            score = Score.find_by(where=where_str)
            if score: score_ = score[0]['score']
            else:return None

        #get rank

        sql = """SELECT id ,rank, user_id FROM
 (SELECT
id ,
score,
user_id,
rank() over (order by score desc) as rank
FROM rankings)  AS ranks
WHERE score  =  %s;""" % score_


        self.cur.execute(sql)
        user_rank = self.cur.fetchone()
        return  user_rank['rank']

    def get_beatrank(self, user_rank):

        sql = "SELECT COUNT(id) FROM rankings;"
        self.cur.execute(sql)
        user_count = self.cur.fetchone()[0]

        beatrank = 0
        if user_count > 1:
            beatrank = float( user_count - user_rank )/float(user_count -1)

        return  beatrank






    def create(self):
        user_info = CWModel.create(self)
        return user_info['id']

    def update_notice(self, _notice):
        self.notice = _notice
        self.notice_got_it_number = 0
        self.notice_updated_at = int(time.time())

        self.update()


    def get_friends(self):
        sql = self.cur.mogrify("SELECT * FROM users AS u \
        JOIN friendships AS f ON u.id = f.friend_id \
        WHERE f.user_id = %s; ", (self.id,))

        print sql
        self.cur.execute(sql)

        return self.cur.fetchall()

        # def create(self):
        #     #self.notice_got_it_number = 0
        #     return CWModel.create(self)["id"]


if __name__ == "__main__":
    pass

