"""Stop only this folder's local portal through its loopback API."""
from pathlib import Path
from urllib.request import urlopen,Request
import json
root=Path(__file__).resolve().parent
try:
 state=json.loads((root/'.portal-state.json').read_text(encoding='utf-8'));port=int(state['port'])
 if not 1024<=port<=65535:raise ValueError('Invalid saved port')
 url=f'http://127.0.0.1:{port}/'
 with urlopen(url+'api/health',timeout=2) as response:health=json.load(response)
 if health.get('app')!='UHAI Portal':raise ValueError('That address is not the portal')
 with urlopen(Request(url+'api/stop',method='POST'),timeout=5) as response:print(json.load(response)['message'])
except Exception as e:print('No matching running portal was stopped:',e)
