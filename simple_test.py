import requests

# Simple test with minimal data
closes = [1800.0 + i for i in range(20)]

print("Testing /predict endpoint with simple data...")
print(f"Closes: {closes[:5]} ... {closes[-5:]}")

try:
    response = requests.post(
        "http://127.0.0.1:8000/predict",
        json={"closes": closes},
        timeout=5
    )
    
    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ SUCCESS!")
        print(f"Signal: {result['signal']}")
        print(f"Confidence: {result['confidence']:.4f}")
        print(f"Raw: {result['raw_prediction']:.6f}")
    else:
        print(f"❌ FAILED")
        print(response.text)
except Exception as e:
    print(f"❌ ERROR: {e}")
