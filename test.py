import requests

url = "http://edric.localhost:8000.com/my-invoices/"
headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_ACCESS_TOKEN_HERE"  
}
data = {
    "pin": "1234"
}

response = requests.post(url, json=data, headers=headers)
print("Status Code:", response.status_code)
print("Response JSON:", response.json())

