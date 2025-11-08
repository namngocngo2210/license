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
    phone_numbers = payload.get("phone_numbers")
    expires_in = payload.get("expires_in")  # số ngày

    if not isinstance(phone_numbers, list) or len(phone_numbers) == 0:
        return jsonify({"status": False, "error": "phone_numbers phải là mảng không rỗng"}), 400
    if not isinstance(expires_in, int) or expires_in <= 0:
        return jsonify({"status": False, "error": "expires_in phải là số nguyên dương"}), 400

    # tránh tạo quá nhiều một lúc
    if len(phone_numbers) > 1000:
        return jsonify({"status": False, "error": "phone_numbers tối đa 1000 số"}), 400

    # Validate phone_numbers
    for phone in phone_numbers:
        if not isinstance(phone, str) or not phone.strip():
            return jsonify({"status": False, "error": "phone_numbers phải là mảng các chuỗi không rỗng"}), 400

    expires_ts = int((datetime.now(timezone.utc) + timedelta(days=expires_in)).timestamp())

    with _lock:
        licenses = _load_licenses()
        existing_codes = {l.get("code") for l in licenses}
        existing_phones = {l.get("phone_number") for l in licenses if l.get("phone_number")}

        created_items = []
        seen_codes = set()
        seen_phones = set()
        
        for phone in phone_numbers:
            phone = phone.strip()
            # Kiểm tra số điện thoại đã tồn tại
            if phone in existing_phones or phone in seen_phones:
                continue
            
            # Tạo code mới, đảm bảo không trùng
            while True:
                c = _generate_codes(1)[0]
                if c not in existing_codes and c not in seen_codes:
                    break
            
            # Lưu license với đầy đủ code, phone_number và expired_at vào danh sách
            license_item = {"code": c, "phone_number": phone, "expired_at": expires_ts}
            licenses.append(license_item)
            created_items.append(license_item)
            seen_codes.add(c)
            seen_phones.add(phone)
        
        # Lưu toàn bộ danh sách licenses (bao gồm phone_number) vào file license.json
        _save_licenses(licenses)

    return jsonify({"status": True, "data": created_items}), 201


@app.post("/verify")
def verify_license():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    phone_number = payload.get("phone_number")
    
    if not code:
        return jsonify({"status": False, "error": "code là bắt buộc"}), 400
    if not phone_number:
        return jsonify({"status": False, "error": "phone_number là bắt buộc"}), 400

    with _lock:
        licenses = _load_licenses()

    lic = next((l for l in licenses if l.get("code") == code and l.get("phone_number") == phone_number), None)
    if lic is None:
        return jsonify({"status": False, "valid": False, "reason": "not_found"}), 404

    exp_ts = _parse_expired_at_to_ts(lic.get("expired_at"))
    if exp_ts is None:
        return jsonify({"status": False, "valid": False, "reason": "invalid_expired_at"}), 500

    now_ts = int(datetime.now(timezone.utc).timestamp())
    is_valid = now_ts <= exp_ts
    status_code = 200 if is_valid else 410
    return jsonify({"status": True, "valid": is_valid, "expired_at": exp_ts}), status_code


@app.get("/list")
def list_licenses():
    """Lấy danh sách tất cả các license code"""
    with _lock:
        licenses = _load_licenses()
    
    return jsonify({"status": True, "data": licenses}), 200


@app.put("/update")
def update_license():
    """Cập nhật thời hạn của license code(s)"""
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    expires_in = payload.get("expires_in")
    
    if not code:
        return jsonify({"status": False, "error": "code là bắt buộc"}), 400
    if not isinstance(expires_in, int) or expires_in <= 0:
        return jsonify({"status": False, "error": "expires_in phải là số nguyên dương"}), 400
    
    # Chuyển code thành list nếu là string đơn
    if isinstance(code, str):
        codes_to_update = [code]
    elif isinstance(code, list):
        codes_to_update = code
    else:
        return jsonify({"status": False, "error": "code phải là string hoặc array"}), 400
    
    if not codes_to_update:
        return jsonify({"status": False, "error": "code không được rỗng"}), 400
    
    expires_ts = int((datetime.now(timezone.utc) + timedelta(days=expires_in)).timestamp())
    
    with _lock:
        licenses = _load_licenses()
        codes_set = set(codes_to_update)
        updated_count = 0
        not_found_codes = []
        
        for lic in licenses:
            if lic.get("code") in codes_set:
                lic["expired_at"] = expires_ts
                updated_count += 1
                codes_set.remove(lic.get("code"))
        
        not_found_codes = list(codes_set)
        
        if updated_count == 0:
            return jsonify({"status": False, "error": "không tìm thấy code nào để cập nhật"}), 404
        
        _save_licenses(licenses)
    
    result = {
        "status": True,
        "message": "updated",
        "updated_count": updated_count,
        "expired_at": expires_ts
    }
    
    if not_found_codes:
        result["not_found_codes"] = not_found_codes
    
    return jsonify(result), 200


@app.delete("/delete")
def delete_license():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code:
        return jsonify({"status": False, "error": "code là bắt buộc"}), 400

    with _lock:
        licenses = _load_licenses()
        new_list = [l for l in licenses if l.get("code") != code]
        if len(new_list) == len(licenses):
            return jsonify({"status": False, "error": "code không tồn tại"}), 404
        _save_licenses(new_list)

    return jsonify({"status": True, "message": "deleted"}), 200


@app.delete("/delete-all")
def delete_all_licenses():
    """Xóa tất cả license code"""
    with _lock:
        licenses = _load_licenses()
        deleted_count = len(licenses)
        _save_licenses([])
    
    return jsonify({"status": True, "message": "deleted_all", "deleted_count": deleted_count}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


