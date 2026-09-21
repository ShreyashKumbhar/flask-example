import os

import requests


API_URL = os.environ.get("API_URL", "http://localhost:5001").rstrip("/")


def _url(path):
    return API_URL + path


def list_users():
    response = requests.get(_url("/users"), timeout=10)
    response.raise_for_status()
    return response.json()


def verify(user_id, pw):
    response = requests.post(
        _url("/auth"),
        json={"id": user_id, "pw": pw},
        timeout=10,
    )
    return response.status_code == 200


def delete_user_from_db(user_id):
    response = requests.delete(_url("/users/" + user_id), timeout=10)
    response.raise_for_status()


def add_user(user_id, pw):
    response = requests.post(
        _url("/users"),
        json={"id": user_id, "pw": pw},
        timeout=10,
    )
    if response.status_code == 409:
        raise ValueError("duplicate")
    if response.status_code == 400:
        raise ValueError("invalid")
    response.raise_for_status()


def read_note_from_db(user_id):
    response = requests.get(_url("/notes"), params={"user": user_id}, timeout=10)
    response.raise_for_status()
    notes = response.json()
    return [(item["note_id"], item["timestamp"], item["note"]) for item in notes]


def write_note_into_db(user_id, note_to_write):
    response = requests.post(
        _url("/notes"),
        json={"user": user_id, "note": note_to_write},
        timeout=10,
    )
    response.raise_for_status()


def match_user_id_with_note_id(note_id):
    response = requests.get(_url("/notes/" + note_id + "/owner"), timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["owner"]


def delete_note_from_db(note_id):
    response = requests.delete(_url("/notes/" + note_id), timeout=10)
    response.raise_for_status()


def image_upload_record(uid, owner, image_name, timestamp):
    response = requests.post(
        _url("/images"),
        json={"uid": uid, "owner": owner, "name": image_name, "timestamp": timestamp},
        timeout=10,
    )
    response.raise_for_status()


def list_images_for_user(owner):
    response = requests.get(_url("/images"), params={"owner": owner}, timeout=10)
    response.raise_for_status()
    images = response.json()
    return [(item["uid"], item["timestamp"], item["name"]) for item in images]


def match_user_id_with_image_uid(image_uid):
    response = requests.get(_url("/images/" + image_uid + "/owner"), timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()["owner"]


def delete_image_from_db(image_uid):
    response = requests.delete(_url("/images/" + image_uid), timeout=10)
    response.raise_for_status()
