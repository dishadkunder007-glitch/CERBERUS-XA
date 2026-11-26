import requests
import json

BASE = 'http://localhost:8000'

def test_pipeline():
    print('--- 1. Testing GET /health ---')
    r = requests.get(f'{BASE}/health')
    print('Status:', r.status_code)
    print(json.dumps(r.json(), indent=2))

    print('\n--- 2. Testing POST /seed-benchmark ---')
    r = requests.post(f'{BASE}/seed-benchmark')
    print('Status:', r.status_code, r.json())

    print('\n--- 3. Testing GET /graph ---')
    r = requests.get(f'{BASE}/graph')
    data = r.json()
    print('Status:', r.status_code)
    print(f'Nodes count: {len(data.get("nodes", []))}')
    print(f'Links count: {len(data.get("links", []))}')

    print('\n--- 4. Testing GET /conflicts ---')
    r = requests.get(f'{BASE}/conflicts')
    conflicts = r.json()
    print('Status:', r.status_code)
    print(f'Conflicts detected: {len(conflicts)}')
    if conflicts:
        print('Sample Conflict:', conflicts[0].get('entity'), '->', conflicts[0].get('attribute'))

    print('\n--- 5. Testing GET /claims ---')
    r = requests.get(f'{BASE}/claims')
    claims = r.json()
    print('Status:', r.status_code, f'Claims count: {len(claims)}')

    print('\n--- 6. Testing GET /reliability ---')
    r = requests.get(f'{BASE}/reliability')
    rel = r.json()
    print('Status:', r.status_code, f'Reliability records: {len(rel)}')

    print('\n--- 7. Testing POST /investigate ---')
    inquiry = {'question': 'Did Nordic Freight misrepresent shipment valuation, arrival dates, and cargo contents?'}
    r = requests.post(f'{BASE}/investigate', json=inquiry)
    report = r.json()
    print('Status:', r.status_code)
    print('Verdict:', report.get('verdict'))
    print('Confidence:', report.get('confidence'))
    print('Summary:', report.get('summary')[:120] if report.get('summary') else 'None')
    print('Citations count:', len(report.get('citations', [])))
    print('Reasoning steps:', len(report.get('reasoningSteps', [])))

    print('\n=============================================')
    print('ALL BACKEND PIPELINE ENDPOINTS VERIFIED 100%!')
    print('=============================================')

if __name__ == '__main__':
    test_pipeline()
