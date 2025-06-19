# app.py
from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor Rota Pharma OK - acesse /posicoes.csv"

@app.route("/posicoes.csv")
def csv():
    caminho = "posicoes.csv"
    if os.path.exists(caminho):
        return send_file(caminho, mimetype="text/csv")
    return "Arquivo CSV ainda não disponível", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)