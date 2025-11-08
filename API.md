# License Management API Documentation

## Tổng quan

API quản lý license code cho phép tạo, xác thực, cập nhật, xóa và liệt kê các license code. Mỗi license code được gắn với một số điện thoại và có thời hạn sử dụng được quản lý bằng Unix timestamp. Việc xác thực license yêu cầu cả code và số điện thoại phải khớp.

**Base URL:** `http://localhost:5000`

**Content-Type:** `application/json`

## Cấu trúc Response

Tất cả các response đều có field `status`:
- `status: true` - Thành công
- `status: false` - Có lỗi xảy ra

## Endpoints

### 1. Tạo License Code

Tạo license code cho danh sách số điện thoại. Mỗi số điện thoại sẽ được gán một license code duy nhất.

**Endpoint:** `POST /create`

**Request Body:**
```json
{
  "phone_numbers": ["0123456789", "0987654321", "0912345678"],
  "expires_in": 30
}
```

**Parameters:**
- `phone_numbers` (array, required): Mảng các số điện thoại cần tạo license (tối đa 1000 số)
- `expires_in` (integer, required): Thời hạn sử dụng tính bằng ngày

**Response Success (201):**
```json
{
  "status": true,
  "data": [
    {
      "code": "550e8400-e29b-41d4-a716-446655440000",
      "phone_number": "0123456789",
      "expired_at": 1735689600
    },
    {
      "code": "550e8400-e29b-41d4-a716-446655440001",
      "phone_number": "0987654321",
      "expired_at": 1735689600
    }
  ]
}
```

**Response Error (400):**
```json
{
  "status": false,
  "error": "phone_numbers phải là mảng không rỗng"
}
```

**Lỗi có thể xảy ra:**
- `400`: `phone_numbers` không phải mảng hoặc mảng rỗng
- `400`: `expires_in` không phải số nguyên dương
- `400`: `phone_numbers` vượt quá 1000 số
- `400`: Có số điện thoại không hợp lệ (rỗng hoặc không phải chuỗi)

**Lưu ý:** 
- Số điện thoại đã tồn tại trong hệ thống sẽ được bỏ qua (không tạo license mới)
- Mỗi số điện thoại chỉ có thể có một license code duy nhất

---

### 2. Xác thực License Code

Kiểm tra tính hợp lệ của một license code. Yêu cầu cả code và số điện thoại phải khớp.

**Endpoint:** `POST /verify`

**Request Body:**
```json
{
  "code": "550e8400-e29b-41d4-a716-446655440000",
  "phone_number": "0123456789"
}
```

**Parameters:**
- `code` (string, required): License code cần xác thực
- `phone_number` (string, required): Số điện thoại gắn với license code

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

Hoặc:
```json
{
  "status": false,
  "error": "phone_number là bắt buộc"
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
- `400`: Thiếu field `code` hoặc `phone_number`
- `404`: Không tìm thấy license với code và phone_number khớp
- `500`: Dữ liệu `expired_at` không hợp lệ

**Lưu ý:** License chỉ được xác thực thành công khi cả `code` và `phone_number` đều khớp với dữ liệu trong hệ thống.

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
      "phone_number": "0123456789",
      "expired_at": 1735689600
    },
    {
      "code": "550e8400-e29b-41d4-a716-446655440001",
      "phone_number": "0987654321",
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

### Tạo license code cho danh sách số điện thoại với thời hạn 30 ngày
```bash
curl -X POST http://localhost:5000/create \
  -H "Content-Type: application/json" \
  -d '{
    "phone_numbers": ["0123456789", "0987654321", "0912345678"],
    "expires_in": 30
  }'
```

### Xác thực license code
```bash
curl -X POST http://localhost:5000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "code": "550e8400-e29b-41d4-a716-446655440000",
    "phone_number": "0123456789"
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

2. **Số điện thoại:** Mỗi license code được gắn với một số điện thoại duy nhất. Mỗi số điện thoại chỉ có thể có một license code.

3. **Cấu trúc dữ liệu:** Mỗi license bao gồm:
   - `code`: License code (UUID v4)
   - `phone_number`: Số điện thoại gắn với license
   - `expired_at`: Thời hạn sử dụng (Unix timestamp)

4. **Thời hạn (expired_at):** Được lưu dưới dạng Unix timestamp (số giây kể từ 1/1/1970 UTC)

5. **Thread Safety:** Tất cả các thao tác đều được bảo vệ bằng lock để đảm bảo thread-safe

6. **Dữ liệu lưu trữ:** License được lưu trong file `license.json` trong cùng thư mục với ứng dụng

7. **Giới hạn:** Mỗi lần tạo tối đa 1000 license code (tương ứng với 1000 số điện thoại)

8. **Xác thực:** Việc xác thực license yêu cầu cả `code` và `phone_number` phải khớp với dữ liệu trong hệ thống

