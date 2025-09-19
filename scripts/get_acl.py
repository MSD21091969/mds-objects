import requests
import json

ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X2FkbWluIiwiZXhwIjoxNzU2MTAxMTExfQ.J-lFaenTfcXbFutzht8QSWN5Qta8EA4tDgULKVqfBrE"
CASEFILE_ID = "case-0a0063ad80"
URL = f"http://127.0.0.1:8000/api/v1/casefiles/{CASEFILE_ID}"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}"
}

response = requests.get(URL, headers=headers)
response.raise_for_status() # Raise an exception for HTTP errors

casefile_json_str = response.json()
casefile_data = json.loads(casefile_json_str)

print(casefile_data['acl'])
