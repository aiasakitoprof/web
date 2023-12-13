import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# URL de la API:
url = "https://services1.arcgis.com/nCKYwcSONQTkPA4K/arcgis/rest/services/PaisVascoEleccionesAutonomicas2016/FeatureServer/0/query?where=1%3D1&outFields=AMBITO,Censo,Votantes,Nulos,Válidos,Blancos,Abstenciones,EAJ_PNV,PP,PH,EK_PCPE,PSE_EE_PSOE,PACMA_ATTKA,PFYV,C´S,EB_AZ,O_E_,EH_BILDU,VOX,GANEMOS,LN,Fecha,codine&returnGeometry=false&outSR=4326&f=json"

# Función para leer HTMLs:
def readHTML(file_path: str):
    path = Path(file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return path.read_text()



# Orden de página y función
# Página principal (index):
@app.get("/")
async def readIndex():
    return HTMLResponse(content=readHTML("index.html"), status_code=200)



# Página del censo:
@app.get("/Html/censo.html")
async def readCenso():
    return HTMLResponse(content=readHTML("Html/censo.html"))

# ======

@app.get("/censo")
async def getCenso():
    params = {
        'where': '1=1',
        'outFields': 'Censo',
        'outSR': '4326',
        'f': 'json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    data = response.json()
    censo = sum(int(feature['attributes']['Censo'] or 0) for feature in data['features'])
    return {"total_censados": censo}



# Página de partidos mas votados:
@app.get("/Html/masVotados.html")
async def readMasVotados():
    return HTMLResponse(content=readHTML("Html/masVotados.html"))

# ======

@app.get("/masVotados")
async def getMasVotados():
    params = {
        'where': '1=1',
        'outFields': '*',
        'outSR': '4326',
        'f': 'json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    data = response.json()

    partidos_votos = {}
    for feature in data['features']:
        for partido, votos in feature['attributes'].items():
            if partido not in ['EAJ_PNV', 'PP', 'PH', 'EK_PCPE', 'PSE_EE_PSOE', 'PACMA_ATTKA', 'PFYV', 'C´S', 'EB_AZ', 'O_E_', 'EH_BILDU', 'VOX', 'GANEMOS', 'LN', 'PODEMOS_AHAL_DUGU_IU', 'RECORTES_CERO_GV']:
                continue
            if votos is not None:
                partidos_votos[partido] = partidos_votos.get(partido, 0) + votos

    top_partidos = sorted(partidos_votos.items(), key=lambda x: x[1], reverse=True)[:3]
    top_partidos_format = [{'partido': partido, 'votos': votos} for partido, votos in top_partidos]

    return top_partidos_format



# Página de votos:
@app.get("/Html/porVotos.html")
async def readPorVotos():
    return HTMLResponse(content=readHTML("Html/porVotos.html"))

# ======

@app.get("/porcentajes")
async def getPorVotos():
    params = {
        'where': '1=1',
        'outFields': 'Censo,Votantes,Nulos,Válidos,Blancos,Abstenciones',
        'outSR': '4326',
        'f': 'json'
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    data = response.json()

    censo = sum(int(feature['attributes']['Censo'] or 0) for feature in data['features'])
    votantes = sum(int(feature['attributes']['Votantes'] or 0) for feature in data['features'])
    nulos = sum(int(feature['attributes']['Nulos'] or 0) for feature in data['features'])
    validos = sum(int(feature['attributes']['Válidos'] or 0) for feature in data['features'])
    blancos = sum(int(feature['attributes']['Blancos'] or 0) for feature in data['features'])
    abstenciones = sum(int(feature['attributes']['Abstenciones'] or 0) for feature in data['features'])

    porcentaje_votantes = (votantes / censo) * 100
    porcentaje_nulos = (nulos / censo) * 100
    porcentaje_validos = (validos / censo) * 100
    porcentaje_blancos = (blancos / censo) * 100
    porcentaje_abstenciones = (abstenciones / censo) * 100

    return {
        "Votos Válidos": porcentaje_validos,
        "Votos nulos": porcentaje_nulos,
        "Votos en Blancos": porcentaje_blancos,
        "Total de Votantes": porcentaje_votantes,
        "Abstenciones": porcentaje_abstenciones
    }



# Incicio del REST service de la página:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)