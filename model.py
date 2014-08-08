#!/usr/bin/python
# -*- coding:utf-8 -*-

import time
import os
import base64

import psycopg2
import psycopg2.extras


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

DROP TABLE IF EXISTS  address_books ;
CREATE TABLE address_books(
   id SERIAL PRIMARY KEY NOT NULL,
   phone_number_1 VARCHAR(32) ,
   phone_number_2 VARCHAR(32) ,
   phone_number_3 VARCHAR(32) ,
   email_1 VARCHAR(150),
   email_2 VARCHAR(150),
   email_3 VARCHAR(150),
   name VARCHAR(80),
   first_name VARCHAR (32),
   last_name VARCHAR (32),
   user_id  INT NOT NULL,
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);


DROP TABLE IF EXISTS friendships ;
CREATE TABLE friendships(
   id SERIAL PRIMARY KEY     NOT NULL,
   user_id  INT NOT NULL,
   friend_id INT NOT NULL,
   status CHAR(2),
   created_at INT NOT NULL,
   updated_at INT NOT NULL
);

    """)
    conn.commit()


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
        conn = psycopg2.connect("dbname=gameranking  user=user host=127.0.0.1  port=5432")
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


# def create(self):
#
#         CWModel.create(self)
#         #user got_it num +1
#
#         sql =self.cur.mogrify("UPDATE users SET notice_got_it_number = (notice_got_it_number+ 1) \
# WHERE id  = %s ;", (self.notice_id ,) )
#         print sql
#         self.cur.execute(sql)
#         self.conn.commit()


class Phonebook(CWModel):
    @classmethod
    def create_many(cls, user_id, phonebooks):
        for index_phonebook in phonebooks:
            phone_number = index_phonebook["phone_number"]
            email = index_phonebook["email"]
            now_time = int(time.time())
            sql = cls.cur.mogrify("INSERT INTO phonebooks (phone_number ,email ,user_id ,\
created_at, updated_at ) VALUES (%s, %s, %s,%s,%s) ;", (phone_number, email, user_id, now_time, now_time))
            print sql
            cls.cur.execute(sql)
        cls.conn.commit()


class Friendship(CWModel):
    """ friendship maker
    """

    @classmethod
    def is_friendship_exist(cls, user_id, friend_id):
        sql = "user_id = %s AND friend_id = %s LIMIT 1" % (user_id, friend_id)
        if cls.find_by(sql):
            return True
        return False

    @classmethod
    def remove_friendship(cls, user_id, friend_id):
        table_name = cls.__name__.lower() + 's'
        sql_up = "DELETE FROM %s" % table_name
        sql_up = sql_up + " WHERE user_id = %s AND friend_id = %s;"
        sql = cls.cur.mogrify(sql_up, (user_id, friend_id,))
        #cls.conn.commit()
        print sql
        cls.cur.execute(sql)
        cls.conn.commit()


class Session(CWModel):
    """docstring for Session"""

    @staticmethod
    def generate_session_id():
        return base64.urlsafe_b64encode(os.urandom(64))

    @classmethod
    def check_it(cls, kwargs):
        print "session rqs:", kwargs
        # from id get session data
        session_info = cls.find_by_id(kwargs['id'])

        if not session_info or (session_info['session_id'] != kwargs['session_id']) \
                or (str(session_info['user_id']) != str(kwargs['user_id'])):
            print 'im here'
            # print str(session_info['session_id'])  , str(kwargs['session_id'])
            return False

        now_time = time.time()
        exp_time = session_info['updated_at'] + 3600
        if now_time > exp_time:
            return SESSION_EXPIRES

        return True


class Score(CWModel):
    pass

class Address_book(CWModel):
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

    def upload_addressbook(self, book):
        #for
        #get val
        #reapeat?
        #create
        for index_book in book:

            first_name = index_book['first_name']
            last_name = index_book['last_name']

            emails = index_book['emails']
            email1 = None
            email2 = None
            email3 = None


            if len(emails) > 0: email1 = emails[0]
            if len(emails) > 1: email2 = emails[1]
            if len(emails) > 2: email3 = emails[2]

            phones = index_book['phone_numbers']
            phone1 = None
            phone2 = None
            phone3 = None
            if len(phones) > 0 : phone1 = phones[0]
            if len(phones) > 1 : phone2 = phones[1]
            if len(phones) > 2 : phone3 = phones[2]


            #repeat? first last phone1 === IS REPAET!
            sql_up = "first_name = %s AND last_name = %s AND phone_number_1 = %s"
            where_str = self.cur.mogrify(sql_up, (first_name,last_name,phone1,))
            is_repeat = Address_book.find_by(where=where_str)
            if not is_repeat:
                address_book = Address_book()
                address_book.first_name = first_name
                address_book.last_name = last_name
                address_book.user_id = self.id

                if email1: address_book.email_1 = email1
                if email2: address_book.email_2 = email2
                if email3: address_book.email_3 = email3

                if phone1: address_book.phone_number_1 = phone1
                if phone2: address_book.phone_number_2 = phone2
                if phone3: address_book.phone_number_3 = phone3

                address_book.create()


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

