from flask import Flask, jsonify, request

from database import (
    add_user,
    delete_image_from_db,
    delete_note_from_db,
    delete_user_from_db,
    image_upload_record,
    init_schema,
    list_images_for_user,
    list_users,
    match_user_id_with_image_uid,
    match_user_id_with_note_id,
    read_note_from_db,
    verify,
    wait_for_db,
    write_note_into_db,
)


app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(list_users())


@app.route("/users", methods=["POST"])
def create_user():
    payload = request.get_json(force=True) or {}
    user_id = payload.get("id", "")
    password = payload.get("pw", "")
    if not user_id or not password:
        return jsonify({"error": "id and pw are required"}), 400
    if user_id.upper() in list_users():
        return jsonify({"error": "duplicate"}), 409
    if " " in user_id or "'" in user_id:
        return jsonify({"error": "invalid"}), 400
    add_user(user_id, password)
    return jsonify({"id": user_id.upper()}), 201


@app.route("/users/<user_id>", methods=["DELETE"])
def remove_user(user_id):
    if user_id.upper() == "ADMIN":
        return jsonify({"error": "forbidden"}), 403
    if user_id.upper() not in list_users():
        return jsonify({"error": "not found"}), 404
    delete_user_from_db(user_id.upper())
    return jsonify({"deleted": user_id.upper()})


@app.route("/auth", methods=["POST"])
def auth():
    payload = request.get_json(force=True) or {}
    user_id = (payload.get("id") or "").upper()
    password = payload.get("pw") or ""
    if user_id in list_users() and verify(user_id, password):
        return jsonify({"ok": True, "id": user_id})
    return jsonify({"ok": False}), 401


@app.route("/notes", methods=["GET"])
def get_notes():
    user_id = request.args.get("user")
    if not user_id:
        return jsonify({"error": "user is required"}), 400
    notes = [
        {"note_id": row[0], "timestamp": row[1], "note": row[2]}
        for row in read_note_from_db(user_id)
    ]
    return jsonify(notes)


@app.route("/notes", methods=["POST"])
def create_note():
    payload = request.get_json(force=True) or {}
    user_id = payload.get("user")
    note = payload.get("note")
    if not user_id or note is None:
        return jsonify({"error": "user and note are required"}), 400
    note_id = write_note_into_db(user_id, note)
    return jsonify({"note_id": note_id}), 201


@app.route("/notes/<note_id>/owner", methods=["GET"])
def note_owner(note_id):
    owner = match_user_id_with_note_id(note_id)
    if owner is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"owner": owner})


@app.route("/notes/<note_id>", methods=["DELETE"])
def remove_note(note_id):
    delete_note_from_db(note_id)
    return jsonify({"deleted": note_id})


@app.route("/images", methods=["GET"])
def get_images():
    owner = request.args.get("owner")
    if not owner:
        return jsonify({"error": "owner is required"}), 400
    images = [
        {"uid": row[0], "timestamp": row[1], "name": row[2]}
        for row in list_images_for_user(owner)
    ]
    return jsonify(images)


@app.route("/images", methods=["POST"])
def create_image():
    payload = request.get_json(force=True) or {}
    required = ("uid", "owner", "name", "timestamp")
    if any(not payload.get(key) for key in required):
        return jsonify({"error": "uid, owner, name, and timestamp are required"}), 400
    image_upload_record(payload["uid"], payload["owner"], payload["name"], payload["timestamp"])
    return jsonify({"uid": payload["uid"]}), 201


@app.route("/images/<image_uid>/owner", methods=["GET"])
def image_owner(image_uid):
    owner = match_user_id_with_image_uid(image_uid)
    if owner is None:
        return jsonify({"error": "not found"}), 404
    return jsonify({"owner": owner})


@app.route("/images/<image_uid>", methods=["DELETE"])
def remove_image(image_uid):
    delete_image_from_db(image_uid)
    return jsonify({"deleted": image_uid})


if __name__ == "__main__":
    wait_for_db()
    init_schema()
    app.run(debug=True, host="0.0.0.0", port=5000)
