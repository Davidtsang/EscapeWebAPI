#!usr/bin/python
# -*- coding: utf-8 -*-

import model
import sys

#fun 1: app-tools.py -c createtable
def main():

    cmd  = sys.argv[1]
    params = sys.argv[2]
    #print  "Argument # %s : %s" % (cmd, params)

    if cmd == '-c':
        if params == 'createtable':
            #print "CMD: CREATE TABLE ?"
            user_in =raw_input("CMD: CREATE TABLE ?(Y/N)")
            #model.create_table()
            if user_in.lower() == 'y':
                model.create_table()

            else:
                print 'USER ABORT.'


if __name__ == "__main__":
    main()