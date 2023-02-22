import requests

def generate(i):
    r = requests.post('https://dbox.cf/api/cards/', json={"password": "password"})
    token: str = r.json()["token"]
    text = token.rjust(1024)

    r = requests.get('https://dbox.cf/img/base.jpg')
    content = r.content

    with open(f"data/dbox_cf_{i+1}.jpg", 'wb') as f:
        f.write(content)
        f.write(text.encode('utf-8'))

if __name__ == "__main__":
    for i in range(5):
        generate(i)