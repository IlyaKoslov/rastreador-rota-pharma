# main.py
from zeep import Client, Settings
from zeep.exceptions import Fault
import pandas as pd, datetime as dt, pytz, os

WSDL = "https://sasintegra.sascar.com.br/SasIntegra/SasIntegraWSService?wsdl"
USER = "COMPANHIA782INTG"
PWD  = "sascar"
TZ   = pytz.timezone("America/Sao_Paulo")
CSV_PATH = "posicoes.csv"

client = Client(WSDL, settings=Settings(strict=False, xml_huge_tree=True))

def safe(obj, attr, default=None):
    try: return getattr(obj, attr)
    except: return default

def obter_posicoes():
    try:
        pacs = client.service.obterPacotePosicoes(USER, PWD, 3000)
    except Fault as e:
        print("[Pacotes]", e)
        pacs = []
    ultimos = {}
    for p in pacs:
        vid = safe(p, "idVeiculo")
        data = safe(p, "dataPacote") or safe(p, "dataPosicao")
        if vid and data:
            if vid not in ultimos or data > ultimos[vid]["data"]:
                ultimos[vid] = {
                    "data": data,
                    "lat":  safe(p, "latitude"),
                    "lon":  safe(p, "longitude"),
                    "uf":   safe(p, "uf"),
                    "cidade": safe(p, "cidade"),
                    "temperatura": safe(p, "temperaturaSensor1"),
                }
    return ultimos

def fallback_localizacao(vid):
    try:
        loc = client.service.obterPacoteLocalizacao(USER, PWD, vid)
        if loc:
            return {
                "data": safe(loc, "dataPacote") or safe(loc, "dataPosicao"),
                "lat": safe(loc, "latitude"),
                "lon": safe(loc, "longitude"),
                "uf": safe(loc, "uf"),
                "cidade": safe(loc, "cidade"),
                "temperatura": None
            }
    except: return None

def atualizar_csv():
    if os.path.exists(CSV_PATH):
        df_antigo = pd.read_csv(CSV_PATH)
    else:
        df_antigo = pd.DataFrame(columns=["id", "placa", "data", "lat", "lon", "uf", "cidade", "temperatura", "status"])

    veiculos = client.service.obterVeiculos(USER, PWD, 1000, 0)
    ult_pos = obter_posicoes()

    novas_linhas = []
    for v in veiculos:
        vid   = safe(v, "idVeiculo")
        placa = safe(v, "placa", "SEM PLACA")
        pos   = ult_pos.get(vid) or fallback_localizacao(vid)

        if pos:
            novas_linhas.append({
                "id": vid, "placa": placa, "data": pos["data"],
                "lat": pos["lat"], "lon": pos["lon"],
                "uf": pos["uf"], "cidade": pos["cidade"],
                "temperatura": pos["temperatura"],
                "status": "Atualizado"
            })

    df_novo = pd.DataFrame(novas_linhas)
    if not df_antigo.empty:
        df_antigo.loc[df_antigo["placa"].isin(df_novo["placa"]), "status"] = "Histórico"

    df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
    df_final["_refresh"] = pd.Timestamp.now(tz=TZ).isoformat()
    df_final.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print("🔁 Base atualizada com", len(df_novo), "placas[forçado]")

if __name__ == "__main__":
    atualizar_csv()
