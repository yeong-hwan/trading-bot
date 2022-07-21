import requests


def send_message(msg):
    try:
        TARGET_URL = 'https://notify-api.line.me/api/notify'
        TOKEN = '4ZlHYSIm49miBssVLyZ8ykmTsFpSt6e3W3iLZBQ9WeU'

        response = requests.post(
            TARGET_URL,
            headers={
                'Authorization': 'Bearer ' + TOKEN
            },
            data={
                'message': msg
            }
        )
        print(response.text)
        return response.text

    except Exception as e:
        print(e)