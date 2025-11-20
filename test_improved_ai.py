"""
Test improved AI prediction with new thresholds and confidence calculation
"""
import requests
import json

# Test data - sample close prices
test_closes = [
    1800.0, 1804.0, 1807.5, 1809.5, 1811.0,
    1813.5, 1814.0, 1816.5, 1818.0, 1819.5,
    1821.0, 1823.0, 1824.5, 1826.0, 1827.5,
    1828.5, 1829.0, 1830.5, 1832.0, 1833.5
]

print("=" * 60)
print("TESTING IMPROVED AI PREDICTION")
print("=" * 60)

# Test /predict endpoint
url = "http://127.0.0.1:8000/predict"
payload = {"closes": test_closes}

print(f"\nSending request to {url}")
print(f"Data: {len(test_closes)} close prices")

try:
    response = requests.post(url, json=payload, timeout=5)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ SUCCESS!")
        print(f"Signal: {result['signal']}")
        print(f"Confidence: {result['confidence']:.4f} ({result['confidence']*100:.2f}%)")
        print(f"Raw Prediction: {result['raw_prediction']:.6f}")
        
        # Check if improvements worked
        print("\n" + "-" * 60)
        print("DIAGNOSIS:")
        if result['confidence'] > 0:
            print(f"✅ Confidence is now > 0 (was 0.00 before)")
        if result['signal'] != 'NEUTRAL' or abs(result['raw_prediction']) > 0.01:
            print(f"✅ Signal detection improved")
        else:
            print(f"⚠️  Still NEUTRAL, but this may be correct for this data")
    else:
        print(f"\n❌ FAILED: Status code {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("\n" + "=" * 60)
