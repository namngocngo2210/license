# License Management API Documentation

## Tổng quan

API quản lý license code cho phép tạo, xác thực, cập nhật, xóa và liệt kê các license code. Mỗi license code có thời hạn sử dụng được quản lý bằng Unix timestamp.

**Base URL:** `http://localhost:5000`

**Content-Type:** `application/json`

## Cấu trúc Response

Tất cả các response đều có field `status`:
- `status: true` - Thành công
- `status: false` - Có lỗi xảy ra

## Endpoints

### 1. Tạo License Code

Tạo một hoặc nhiều license code mới.

**Endpoint:** `POST /create`

**Request Body:**
```json
{
  "quantity": 5,
  "expires_in": 30
}
```

**Parameters:**
- `quantity` (integer, required): Số lượng license code cần tạo (1-1000)
- `expires_in` (integer, required): Thời hạn sử dụng tính bằng ngày

**Response Success (201):**
```json
{
  "status": true,
  "data": [
    {
      "code": "550e8400-e29b-41d4-a716-446655440000",
      "expired_at": 1735689600
    },
    {
      "code": "550e8400-e29b-41d4-a716-446655440001",
      "expired_at": 1735689600
    }
  ]
}
```

**Response Error (400):**
```json
{
  "status": false,
  "error": "quantity phải là số nguyên dương"
}
```

**Lỗi có thể xảy ra:**
- `400`: `quantity` hoặc `expires_in` không hợp lệ
- `400`: `quantity` vượt quá 1000

---

### 2. Xác thực License Code

Kiểm tra tính hợp lệ của một license code.

**Endpoint:** `POST /verify`

**Request Body:**
```json
{
  "code": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Parameters:**
- `code` (string, required): License code cần xác thực

**Response Success - License hợp lệ (200):**
```json
{
  "status": true,
  "valid": true,
  "expired_at": 1735689600
}
```

**Response Success - License đã hết hạn (410):**
```json
{
  "status": true,
  "valid": false,
  "expired_at": 1735689600
}
```

**Response Error (400):**
```json
{
  "status": false,
  "error": "code là bắt buộc"
}
```

**Response Error (404):**
```json
{
  "status": false,
  "valid": false,
  "reason": "not_found"
}
```

**Response Error (500):**
```json
{
  "status": false,
  "valid": false,
  "reason": "invalid_expired_at"
}
```

**Lỗi có thể xảy ra:**
- `400`: Thiếu field `code`
- `404`: License code không tồn tại
- `500`: Dữ liệu `expired_at` không hợp lệ

---

### 3. Lấy danh sách License Code

Lấy danh sách tất cả các license code đã được tạo.

**Endpoint:** `GET /list`

**Request Body:** Không có

**Response Success (200):**
```json
{
  "status": true,
  "data": [
    {
      "code": "550e8400-e29b-41d4-a716-446655440000",
      "expired_at": 1735689600
    },
    {
      "code": "550e8400-e29b-41d4-a716-446655440001",
      "expired_at": 1735689600
    }
  ]
}
```

---

### 4. Cập nhật thời hạn License Code

Cập nhật thời hạn sử dụng cho một hoặc nhiều license code.

**Endpoint:** `PUT /update`

**Request Body:**
```json
{
  "code": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
  "expires_in": 60
}
```

Hoặc cập nhật một code đơn:
```json
{
  "code": "550e8400-e29b-41d4-a716-446655440000",
  "expires_in": 60
}
```

**Parameters:**
- `code` (string | array, required): License code hoặc mảng các license code cần cập nhật
- `expires_in` (integer, required): Thời hạn mới tính bằng ngày (từ thời điểm hiện tại)

**Response Success (200):**
```json
{
  "status": true,
  "message": "updated",
  "updated_count": 2,
  "expired_at": 1735689600
}
```

**Response Success với một số code không tìm thấy (200):**
```json
{
  "status": true,
  "message": "updated",
  "updated_count": 1,
  "expired_at": 1735689600,
  "not_found_codes": ["550e8400-e29b-41d4-a716-446655440002"]
}
```

**Response Error (400):**
```json
{
  "status": false,
  "error": "code là bắt buộc"
}
```

**Response Error (404):**
```json
{
  "status": false,
  "error": "không tìm thấy code nào để cập nhật"
}
```

**Lỗi có thể xảy ra:**
- `400`: Thiếu field `code` hoặc `expires_in`
- `400`: `expires_in` không phải số nguyên dương
- `400`: `code` không phải string hoặc array
- `404`: Không tìm thấy code nào để cập nhật

---

### 5. Xóa License Code

Xóa một license code khỏi hệ thống.

**Endpoint:** `DELETE /delete`

**Request Body:**
```json
{
  "code": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Parameters:**
- `code` (string, required): License code cần xóa

**Response Success (200):**
```json
{
  "status": true,
  "message": "deleted"
}
```

**Response Error (400):**
```json
{
  "status": false,
  "error": "code là bắt buộc"
}
```

**Response Error (404):**
```json
{
  "status": false,
  "error": "code không tồn tại"
}
```

**Lỗi có thể xảy ra:**
- `400`: Thiếu field `code`
- `404`: License code không tồn tại

---

### 6. Xóa tất cả License Code

Xóa toàn bộ license code khỏi hệ thống.

**Endpoint:** `DELETE /delete-all`

**Request Body:** Không có

**Parameters:** Không có

**Response Success (200):**
```json
{
  "status": true,
  "message": "deleted_all",
  "deleted_count": 10
}
```

**Lưu ý:** Endpoint này sẽ xóa tất cả license code trong hệ thống. Hành động này không thể hoàn tác.

---

## Mã trạng thái HTTP

| Mã | Mô tả |
|---|---|
| 200 | Thành công |
| 201 | Đã tạo thành công |
| 400 | Lỗi request (thiếu hoặc sai tham số) |
| 404 | Không tìm thấy |
| 410 | License đã hết hạn (chỉ trong `/verify`) |
| 500 | Lỗi server |

## Ví dụ sử dụng

### Tạo 10 license code với thời hạn 30 ngày
```bash
curl -X POST http://localhost:5000/create \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 10,
    "expires_in": 30
  }'
```

### Xác thực license code
```bash
curl -X POST http://localhost:5000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "code": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Lấy danh sách tất cả license
```bash
curl -X GET http://localhost:5000/list
```

### Cập nhật thời hạn cho nhiều license
```bash
curl -X PUT http://localhost:5000/update \
  -H "Content-Type: application/json" \
  -d '{
    "code": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
    "expires_in": 60
  }'
```

### Xóa license code
```bash
curl -X DELETE http://localhost:5000/delete \
  -H "Content-Type: application/json" \
  -d '{
    "code": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Xóa tất cả license code
```bash
curl -X DELETE http://localhost:5000/delete-all
```

## Lưu ý

1. **License Code Format:** License code được tạo dưới dạng UUID v4 (ví dụ: `550e8400-e29b-41d4-a716-446655440000`)

2. **Thời hạn (expired_at):** Được lưu dưới dạng Unix timestamp (số giây kể từ 1/1/1970 UTC)

3. **Thread Safety:** Tất cả các thao tác đều được bảo vệ bằng lock để đảm bảo thread-safe

4. **Dữ liệu lưu trữ:** License được lưu trong file `license.json` trong cùng thư mục với ứng dụng

5. **Giới hạn:** Mỗi lần tạo tối đa 1000 license code

