import json
import requests

# Test data
test_data = {
    "guest_name": "Test Guest",
    "room_number": "101",
    "department": "Housekeeping",
    "category": "Clean Room",
    "priority": "Normal"
}

# Send POST request
response = requests.post(
    "http://127.0.0.1:8000/dashboard/api/tickets/create/",
    headers={"Content-Type": "application/json"},
    json=test_data
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")