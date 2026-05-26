"""
Students:
numero:   nome:
numero:   nome:
"""

import sqlite3
import urllib.request
from typing import Optional
import matplotlib.pyplot as plt

URLELEMS = "http://asc.di.fct.unl.pt/~vad/ice/26/elements.txt"
URLXRLINES = "http://asc.di.fct.unl.pt/~vad/ice/26/xray-lines.txt"
TOLERANCE = 0.025
DBNAME = "sepectrum.db"


def do_initdb(con: sqlite3.Connection):
    """ Creates the tables in database. Deletes the old tables if exist.
    In this database, you create four tables and load initial values."""
    cur = con.cursor()

    # Apagar tabelas existentes
    cur.execute("DROP TABLE IF EXISTS Resultados")
    cur.execute("DROP TABLE IF EXISTS Analisados")
    cur.execute("DROP TABLE IF EXISTS Linhas")
    cur.execute("DROP TABLE IF EXISTS Elementos")

    # Criar tabelas
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

    # Descarregar e carregar elementos
    with urllib.request.urlopen(URLELEMS) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            simbolo, nome = line.split(";", 1)
            cur.execute("INSERT INTO Elementos VALUES (?, ?)", (simbolo, nome))

    # Descarregar e carregar linhas de emissão de raios X
    with urllib.request.urlopen(URLXRLINES) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line:
                continue
            parts = line.split(";")
            simbolo = parts[0]
            # pares: energia, peso, energia, peso ...
            for i in range(1, len(parts), 2):
                energia = float(parts[i])
                peso = float(parts[i + 1])
                cur.execute("INSERT INTO Linhas VALUES (?, ?, ?)", (simbolo, energia, peso))

    con.commit()
    print("Database initialized.")


def ler_espectrograma(ficheiro: str) -> list[tuple[float, float]]:
    """Lê um ficheiro de espectrograma e devolve uma lista de pares (energia, contagem)."""
    dados = []
    with open(ficheiro) as f:
        next(f)  # ignorar linha de cabeçalho
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            energia, contagem = linha.split(",")
            dados.append((float(energia), float(contagem)))
    return dados


def detetar_picos(espectro: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Deteta os picos no espectrograma usando o algoritmo avançado.

    Um ponto (energia_i, contagem_i) é um pico se:
    - contagem_{i-1} < contagem_i > contagem_{i+1}  (máximo local)
    - contagem_i >= 5% do pico mais forte
    - energia_i >= 0.5 keV
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
    """Devolve a contagem para a energia dada, ou a do valor imediatamente superior se não existir."""
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
    """Identifica o elemento mais provável para um pico de energia.

    Devolve o símbolo do elemento com maior score, ou None se nenhum
    candidato estiver dentro da TOLERÂNCIA.
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


def do_analyze(ficheiro: str, con: sqlite3.Connection):
    """Lê e analisa o ficheiro de espectrograma. Guarda os resultados na base de dados."""
    espectro = ler_espectrograma(ficheiro)
    picos = detetar_picos(espectro)

    cur = con.cursor()
    cur.execute("INSERT INTO Analisados (ficheiro) VALUES (?)", (ficheiro,))
    numeroanalise = cur.lastrowid

    for pico_energia, pico_contagem in picos:
        simbolo = identificar_elemento(pico_energia, espectro, con)
        if simbolo is None:
            continue
        cur.execute(
            "INSERT INTO Resultados VALUES (?, ?, ?, ?)",
            (numeroanalise, pico_energia, pico_contagem, simbolo)
        )

    con.commit()
    print(f"Analysed {ficheiro}.")


def do_report(ficheiro: str, con: sqlite3.Connection):
    """Escreve no ecrã um relatório com todos os resultados da análise do ficheiro indicado."""
    cur = con.cursor()
    cur.execute("""
        SELECT r.picoenergia, e.nome, r.picocontagem
        FROM Resultados r
        JOIN Analisados a ON r.numeroanalise = a.numeroanalise
        JOIN Elementos e  ON r.simbolo = e.simbolo
        WHERE a.ficheiro = ?
        ORDER BY r.picocontagem DESC
    """, (ficheiro,))
    rows = cur.fetchall()

    print(f"Results for file {ficheiro}:")
    print(f"{'peak':<8} {'element':<15} {'count'}")
    for energia, nome, contagem in rows:
        print(f"{energia:<8.2f} {nome:<15} {contagem}")


def do_stats(simbolo: str, con: sqlite3.Connection):
    """Apresenta estatísticas do elemento dado para todas as análises na base de dados."""
    cur = con.cursor()
    cur.execute("SELECT nome FROM Elementos WHERE simbolo = ?", (simbolo,))
    row = cur.fetchone()
    nome = row[0]

    cur.execute("""
        SELECT COUNT(DISTINCT numeroanalise), MAX(picocontagem), MIN(picocontagem)
        FROM Resultados
        WHERE simbolo = ?
    """, (simbolo,))
    total, maximo, minimo = cur.fetchone()

    print(f"{total} results with {nome}")
    print(f"max count {maximo}")
    print(f"min count {minimo}")


def do_chart(ficheiro: str, con: sqlite3.Connection):
    """Mostra o gráfico do espectrograma com os picos e os nomes dos elementos identificados.
    Não guarda resultados na base de dados.
    """
    espectro = ler_espectrograma(ficheiro)
    picos = detetar_picos(espectro)

    energias = [e for e, _ in espectro]
    contagens = [c for _, c in espectro]

    plt.figure()
    plt.plot(energias, contagens)
    plt.xlabel("Energy (keV)")
    plt.ylabel("Counts")
    plt.title(ficheiro)

    cur = con.cursor()
    for pico_energia, pico_contagem in picos:
        simbolo = identificar_elemento(pico_energia, espectro, con)
        plt.plot(pico_energia, pico_contagem, "ko")  # círculo preto
        if simbolo:
            cur.execute("SELECT nome FROM Elementos WHERE simbolo = ?", (simbolo,))
            nome = cur.fetchone()[0]
            plt.text(pico_energia, pico_contagem, nome)

    plt.tight_layout()
    plt.show()


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
        elif words[0].lower() == "analyze" and len(words) == 2:
            do_analyze(words[1], con)
        elif words[0].lower() == "report" and len(words) == 2:
            do_report(words[1], con)
        elif words[0].lower() == "stats" and len(words) == 2:
            do_stats(words[1], con)
        elif words[0].lower() == "chart" and len(words) == 2:
            do_chart(words[1], con)

        else:
            print("unknown command")
    con.close()


#%%
#   run main function

if __name__ == "__main__":
    main(DBNAME)
