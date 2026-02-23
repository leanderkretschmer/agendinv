# AgendaInv Universal API Backend (MVP)

Dieses Projekt stellt ein universelles API-Backend mit Weboberfläche bereit:

- Nutzerverwaltung mit Login + API-Key
- Pro Nutzer eigene Data-Endpunkte
- Universeller Abruf unter `/api/universal/{endpoint_id}`
- Provider-Skeletons für:
  - webuntis
  - imap
  - caldav
  - immich
  - tesla
  - cupra
  - proxmox
  - weather
- Admin-Funktion in der WebUI, um `git pull` auszuführen

## Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Dann öffnen: `http://127.0.0.1:8000`

## Schnellstart mit Script

```bash
chmod +x install.sh
./install.sh
```

Optional kannst du Host/Port setzen:

```bash
HOST=0.0.0.0 PORT=8000 ./install.sh
```


## Beispiel-Flow

1. Benutzer registrieren (erstmals via API):

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"supersecret123","is_admin":true}'
```

2. Login:

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"supersecret123"}'
```

3. Endpoint anlegen (Bearer Token nötig).
4. Daten holen über `GET /api/universal/{id}` + Header `x-api-key`.

## Hinweis

Aktuell sind die Provider als **Connector-Skeleton** implementiert. Für echte Datenquellen müssen die einzelnen Integrationen (Auth, API-Aufrufe, Mapping, Caching) noch pro Provider ergänzt werden.
