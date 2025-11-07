from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta
import threading
import json
import os
import secrets
import string
import uuid


app = Flask(__name__)

_lock = threading.Lock()
_LICENSE_FILE = os.path.join(os.path.dirname(__file__), "license.json")


def _ensure_store_exists():
    if not os.path.exists(_LICENSE_FILE):
        with open(_LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def _load_licenses():
    _ensure_store_exists()
    try:
        with open(_LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_licenses(licenses):
    with open(_LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(licenses, f, ensure_ascii=False, indent=2)


def _parse_iso_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        # Hỗ trợ định dạng ISO, chấp nhận "Z" là UTC
        value = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _parse_expired_at_to_ts(value):
    """Trả về expired_at dạng Unix timestamp (int) từ dữ liệu lưu trữ.
    Hỗ trợ cả timestamp (int/str số) và ISO 8601 (chuỗi cũ)."""
    # timestamp dạng int hoặc chuỗi số
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        s = value.strip()
        if s.isdigit():
            try:
                return int(s)
            except Exception:
                pass
        dt = _parse_iso_datetime(s)
        if dt is not None:
            return int(dt.timestamp())
    return None


def _generate_codes(count):
    # UUID v4 dạng chuẩn có dấu gạch (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
    return [str(uuid.uuid4()) for _ in range(count)]


@app.post("/create")
def create_license():
    payload = request.get_json(silent=True) or {}
    quantity = payload.get("quantity")
    expires_in = payload.get("expires_in")  # số ngày

    if not isinstance(quantity, int) or quantity <= 0:
        return jsonify({"error": "quantity phải là số nguyên dương"}), 400
    if not isinstance(expires_in, int) or expires_in <= 0:
        return jsonify({"error": "expires_in phải là số nguyên dương"}), 400

    # tránh tạo quá nhiều một lúc
    if quantity > 1000:
        return jsonify({"error": "quantity tối đa 1000"}), 400

    expires_ts = int((datetime.now(timezone.utc) + timedelta(days=expires_in)).timestamp())

    with _lock:
        licenses = _load_licenses()
        existing = {l.get("code") for l in licenses}

        created_items = []
        seen = set()
        while len(created_items) < quantity:
            c = _generate_codes(1)[0]
            if c in existing or c in seen:
                continue
            licenses.append({"code": c, "expired_at": expires_ts})
            created_items.append({"code": c, "expired_at": expires_ts})
            seen.add(c)
        _save_licenses(licenses)

    return jsonify(created_items), 201


@app.post("/verify")
def verify_license():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"error": "code là bắt buộc"}), 400

    with _lock:
        licenses = _load_licenses()

    lic = next((l for l in licenses if l.get("code") == code), None)
    if lic is None:
        return jsonify({"valid": False, "reason": "not_found"}), 404

    exp_ts = _parse_expired_at_to_ts(lic.get("expired_at"))
    if exp_ts is None:
        return jsonify({"valid": False, "reason": "invalid_expired_at"}), 500

    now_ts = int(datetime.now(timezone.utc).timestamp())
    is_valid = now_ts <= exp_ts
    status = 200 if is_valid else 410
    return jsonify({"valid": is_valid, "expired_at": exp_ts}), status


@app.delete("/delete")
def delete_license():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"error": "code là bắt buộc"}), 400

    with _lock:
        licenses = _load_licenses()
        new_list = [l for l in licenses if l.get("code") != code]
        if len(new_list) == len(licenses):
            return jsonify({"error": "code không tồn tại"}), 404
        _save_licenses(new_list)

    return jsonify({"message": "deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


