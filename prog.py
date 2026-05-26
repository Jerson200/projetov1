"""
Students:
numero:   nome:
numero:   nome:
"""

import sqlite3

URLELEMS = "http://asc.di.fct.unl.pt/~vad/ice/26/elements.txt"
URLXRLINES = "http://asc.di.fct.unl.pt/~vad/ice/26/xray-lines.txt"
TOLERANCE = 0.025
DBNAME = "sepectrum.db"

def do_initdb(con: sqlite3.Connection):
    """ Creates the tables in database. Deletes the old tables if exist.
    In this database, you create four tables and load initial values."""
    # TODO...
    pass

#%%

def main(db_name: str):
    """ main funcion that interacts with user"""
    
    con = sqlite3.connect(db_name)
    end=False
    while not end:
        cmd = input("cmd> ")
        words = cmd.strip().split()
        
        if words[0].lower() == "quit":
            end = True
        elif words[0].lower() == "initdb":
            do_initdb(con)
            
        # TODO
        
        else:
            print("unknown command")
    con.close()


#%%
#   run main function

main(DBNAME)
