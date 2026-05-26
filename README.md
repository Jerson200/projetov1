# Analisador de Espectrogramas de Raios X

Ferramenta de linha de comando para análise de espectros de fluorescência de raios X (XRF). O programa lê ficheiros de espectrograma, deteta picos de energia, identifica os elementos químicos presentes e armazena os resultados numa base de dados SQLite.

## Funcionalidades

- Inicialização de base de dados com dados de elementos e linhas de emissão descarregados automaticamente
- Leitura e análise de ficheiros de espectrograma (CSV com colunas `keV, Counts`)
- Deteção de picos usando critérios de máximo local, limiar mínimo (5% do pico máximo) e energia >= 0,5 keV
- Identificação do elemento mais provável por pico (tolerância de ±0,025 keV)
- Relatórios textuais por ficheiro
- Estatísticas por elemento (total de análises, contagem máxima e mínima)
- Gráfico interativo do espectrograma com picos e nomes dos elementos anotados (via matplotlib)

## Pré-requisitos

- Python 3.12+
- matplotlib

```bash
pip install matplotlib
```

## Instalação

```bash
git clone <url-do-repositorio>
cd projetov1
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install matplotlib
```

## Utilização

```bash
python prog.py
```

O programa arranca em modo interativo com a prompt `cmd>`. Comandos disponíveis:

| Comando | Descrição |
|---|---|
| `initdb` | Cria as tabelas e carrega os dados de elementos e linhas de emissão da internet |
| `analyze <ficheiro>` | Analisa o espectrograma e guarda os resultados na base de dados |
| `report <ficheiro>` | Apresenta os resultados da análise de um ficheiro |
| `stats <simbolo>` | Mostra estatísticas de um elemento em todas as análises |
| `chart <ficheiro>` | Mostra o gráfico do espectrograma com os picos identificados |
| `quit` | Termina o programa |

### Exemplo de sessão

```
cmd> initdb
Database initialized.
cmd> analyze unknown1.txt
Analysed unknown1.txt.
cmd> report unknown1.txt
Results for file unknown1.txt:
peak     element         count
1.741    Silicon         20102.0
...
cmd> stats Si
3 results with Silicon
max count 20102.0
min count 12503.0
cmd> chart unknown1.txt
cmd> quit
```

## Ficheiros de espectrograma incluídos

| Ficheiro | Conteúdo |
|---|---|
| `Al.txt`, `Cu.txt`, `Fe.txt`, `Si.txt` | Espectros de referência de elementos conhecidos |
| `MgO.txt`, `FeS2.txt`, `SrF3.txt` | Espectros de referência de compostos conhecidos |
| `unknown1.txt`, `unknown2.txt`, `unknown3.txt` | Amostras desconhecidas para identificação |

O formato dos ficheiros é CSV com cabeçalho `kilo-Electron Volt [keV],Counts`.

## Base de dados

O ficheiro `sepectrum.db` (SQLite) contém quatro tabelas:

- `Elementos` — símbolo e nome de cada elemento
- `Linhas` — energias e pesos das linhas de emissão de raios X por elemento
- `Analisados` — registo de cada análise efetuada (ficheiro e número sequencial)
- `Resultados` — picos detetados e elemento identificado por análise

## Estrutura do projeto

```
projetov1/
├── prog.py          # Código principal
├── sepectrum.db     # Base de dados SQLite
├── *.txt            # Ficheiros de espectrograma
└── enunciado.pdf    # Enunciado do projeto
```
