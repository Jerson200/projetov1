"""
Students:
numero:   nome:
numero:   nome:
"""

import sqlite3
import urllib.request
from typing import Optional

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


def ler_espectrograma(ficheiro: str) -> list[tuple[float, float]]:
    """Reads a spectrogram file and returns a list of (energy, count) pairs."""
    dados = []
    with open(ficheiro) as f:
        next(f)  # skip header line
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            energia, contagem = linha.split(",")
            dados.append((float(energia), float(contagem)))
    return dados


def detetar_picos(espectro: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Detects peaks in the spectrogram using the advanced algorithm.

    A point (energy_i, count_i) is a peak if:
    - count_{i-1} < count_i > count_{i+1}  (local maximum)
    - count_i >= 5% of the strongest peak
    - energy_i >= 0.5 keV
    """
    if not espectro:
        return []

    max_contagem = max(c for _, c in espectro)
    limiar = 0.05 * max_contagem

    picos = []
    for i in range(1, len(espectro) - 1):
        energia, contagem = espectro[i]
        if energia < 0.5:
            continue
        if contagem >= limiar and espectro[i-1][1] < contagem > espectro[i+1][1]:
            picos.append((energia, contagem))
    return picos


def contagem_para_energia(espectro: list[tuple[float, float]], energia_alvo: float) -> float:
    """Returns the count for the given energy, or the next higher energy if exact not found."""
    for energia, contagem in espectro:
        if energia >= energia_alvo:
            return contagem
    return 0.0


def calcular_score(simbolo: str, espectro: list[tuple[float, float]], con: sqlite3.Connection) -> float:
    cur = con.cursor()
    cur.execute("SELECT energia, peso FROM Linhas WHERE simbolo = ?", (simbolo,))
    linhas = cur.fetchall()

    score = 0.0
    for energia_linha, peso in linhas:
        contagem = contagem_para_energia(espectro, energia_linha)
        score += contagem / peso
    return score


def identificar_elemento(pico_energia: float, espectro: list[tuple[float, float]],
                         con: sqlite3.Connection) -> Optional[str]:
    """Finds the best matching element for a peak energy.

    Returns the symbol of the element with the highest score, or None if no
    candidate is within TOLERANCE.
    """
    cur = con.cursor()
    cur.execute("""
        SELECT DISTINCT simbolo FROM Linhas
        WHERE energia BETWEEN ? AND ?
    """, (pico_energia - TOLERANCE, pico_energia + TOLERANCE))
    candidatos = [row[0] for row in cur.fetchall()]

    if not candidatos:
        return None

    melhor = max(candidatos, key=lambda s: calcular_score(s, espectro, con))
    return melhor


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

if __name__ == "__main__":
    main(DBNAME)
