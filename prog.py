"""
Students:
numero:   nome:
numero:   nome:
"""

import sqlite3
import urllib.request

URLELEMS = "http://asc.di.fct.unl.pt/~vad/ice/26/elements.txt"
URLXRLINES = "http://asc.di.fct.unl.pt/~vad/ice/26/xray-lines.txt"
TOLERANCE = 0.025
DBNAME = "sepectrum.db"


def do_initdb(con: sqlite3.Connection):
    """ Creates the tables in database. Deletes the old tables if exist.
    In this database, you create four tables and load initial values."""
    cur = con.cursor()

    # Drop existing tables
    cur.execute("DROP TABLE IF EXISTS Resultados")
    cur.execute("DROP TABLE IF EXISTS Analisados")
    cur.execute("DROP TABLE IF EXISTS Linhas")
    cur.execute("DROP TABLE IF EXISTS Elementos")

    # Create tables
    cur.execute("""
        CREATE TABLE Elementos (
            simbolo TEXT PRIMARY KEY,
            nome    TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE Linhas (
            simbolo TEXT NOT NULL,
            energia REAL NOT NULL,
            peso    REAL NOT NULL,
            FOREIGN KEY (simbolo) REFERENCES Elementos(simbolo)
        )
    """)
    cur.execute("""
        CREATE TABLE Analisados (
            numeroanalise INTEGER PRIMARY KEY AUTOINCREMENT,
            ficheiro      TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE Resultados (
            numeroanalise INTEGER NOT NULL,
            picoenergia   REAL NOT NULL,
            picocontagem  REAL NOT NULL,
            simbolo       TEXT NOT NULL,
            FOREIGN KEY (numeroanalise) REFERENCES Analisados(numeroanalise)
        )
    """)

    # Download and load elements
    with urllib.request.urlopen(URLELEMS) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            simbolo, nome = line.split(";", 1)
            cur.execute("INSERT INTO Elementos VALUES (?, ?)", (simbolo, nome))

    # Download and load x-ray emission lines
    with urllib.request.urlopen(URLXRLINES) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            parts = line.split(";")
            simbolo = parts[0]
            # pairs: energy, weight, energy, weight ...
            for i in range(1, len(parts), 2):
                energia = float(parts[i])
                peso = float(parts[i + 1])
                cur.execute("INSERT INTO Linhas VALUES (?, ?, ?)", (simbolo, energia, peso))

    con.commit()
    print("Database initialized.")


#%%

def main(db_name: str):
    """ main funcion that interacts with user"""

    con = sqlite3.connect(db_name)
    end = False
    while not end:
        cmd = input("cmd> ")
        words = cmd.strip().split()

        if not words:
            continue

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
