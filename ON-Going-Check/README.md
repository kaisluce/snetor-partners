# ON-Going-Check

Script de controle compliance BP (S4 + B1) avec export Excel, logs, et email final.

## Installation

```powershell
cd ON-Going-Check
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration email

Creer `config.cfg` (dans `ON-Going-Check/` ou a la racine projet) avec:

```ini
[azure]
tenantId=...
clientId=...
certificatePath=MDMPythonGraphV2.pfx
certificatePassword=...
```

## Lancement

```powershell
py -3 main.py
```

## Sorties

- Logs: `ON-Going-Check/logs/`
- Exports run: `\\snetor-docs\Users\MDM\001_BUSINESS PARTNER\000_Compliance\BP-ON_GOING_SCREEN\<timestamp>\`
- Email final avec piece jointe `issue_on_compliance.xlsx` si anomalies, sinon sans piece jointe
