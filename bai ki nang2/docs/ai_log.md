# NHẬT KÝ SỬ DỤNG AI

## 1. Mục đích sử dụng AI

Hệ thống quản lý căng tin trường học sử dụng Gemini AI để hỗ trợ phân tích dữ liệu và đưa ra đề xuất cho người quản lý.

Các chức năng AI được triển khai:

* AI đề xuất thực đơn.
* AI tổng hợp phản hồi khách hàng.
* AI phân tích và lập báo cáo doanh thu.

---

## 2. Chức năng AI đề xuất thực đơn

### Prompt sử dụng

```text
Bạn là trợ lý AI quản lý căng tin trường học.

Hãy phân tích dữ liệu căng tin và đưa ra đề xuất thực đơn cho ngày tiếp theo.

Yêu cầu:
1. Chọn 3-5 món phù hợp để đưa vào thực đơn.
2. Ưu tiên món bán chạy.
3. Không ưu tiên món có nguyên liệu đang ở mức thấp.
4. Giải thích ngắn gọn lý do lựa chọn.
5. Đề xuất món cần hạn chế nếu nguyên liệu không đủ.
6. Đưa ra cảnh báo nếu có nguyên liệu sắp hết.

Trả lời bằng tiếng Việt, trình bày rõ ràng, dễ đọc.
```

### Dữ liệu cung cấp cho AI

* Danh sách món ăn.
* Giá món ăn.
* Số lượng món còn lại.
* Trạng thái món ăn.
* Danh sách nguyên liệu.
* Số lượng nguyên liệu.
* Mức tồn kho tối thiểu.
* 5 món bán chạy nhất.

### Kết quả AI

Gemini AI phân tích dữ liệu bán hàng và tồn kho, sau đó đề xuất các món nên ưu tiên trong thực đơn và cảnh báo những nguyên liệu có số lượng thấp.

### Kiểm tra và chỉnh sửa

Sinh viên kiểm tra kết quả AI trước khi sử dụng. Các đề xuất của AI chỉ mang tính hỗ trợ, người quản lý vẫn quyết định thực đơn cuối cùng.

---

## 3. Chức năng AI tổng hợp phản hồi

### Prompt sử dụng

```text
Bạn là AI trợ lý quản lý căng tin trường học.

Hãy phân tích các phản hồi của khách hàng.

Yêu cầu:
1. Đánh giá mức độ hài lòng chung.
2. Xác định các món được đánh giá tốt.
3. Xác định các món hoặc vấn đề nhận nhiều phản hồi chưa tốt.
4. Tóm tắt những ý kiến khách hàng thường nhắc đến.
5. Đề xuất 3 giải pháp cải thiện chất lượng phục vụ.
6. Đưa ra kết luận ngắn gọn cho người quản lý.

Không tự bịa dữ liệu.
Chỉ sử dụng thông tin có trong dữ liệu được cung cấp.
```

### Dữ liệu cung cấp cho AI

* Tên món ăn.
* Số sao đánh giá.
* Nội dung phản hồi của khách hàng.

### Kết quả AI

Gemini AI tổng hợp các phản hồi, xác định xu hướng tích cực và tiêu cực, đồng thời đưa ra các giải pháp cải thiện chất lượng phục vụ.

### Kiểm tra và chỉnh sửa

Sinh viên đối chiếu kết quả AI với dữ liệu phản hồi thực tế trong cơ sở dữ liệu để hạn chế trường hợp AI đưa ra nhận xét không có trong dữ liệu.

---

## 4. Chức năng AI báo cáo doanh thu

### Prompt sử dụng

```text
Bạn là AI trợ lý phân tích doanh thu cho căng tin trường học.

Hãy tạo báo cáo doanh thu ngắn gọn bằng tiếng Việt.

Yêu cầu:
1. Nêu tổng doanh thu.
2. Nêu tổng số lượng món đã bán.
3. Nêu số giao dịch.
4. Xác định món bán chạy nhất.
5. Phân tích xu hướng doanh thu dựa trên dữ liệu.
6. Đưa ra 3 đề xuất giúp tăng doanh thu.
7. Nếu dữ liệu chưa đủ để kết luận xu hướng thì phải nói rõ.

Không tự bịa dữ liệu.
Chỉ sử dụng số liệu được cung cấp.
Trình bày rõ ràng, dễ đọc.
```

### Dữ liệu cung cấp cho AI

* Tổng doanh thu.
* Tổng số lượng món đã bán.
* Tổng số giao dịch.
* 5 món bán chạy nhất.
* Doanh thu trong 7 ngày gần nhất.

### Kết quả AI

Gemini AI tạo báo cáo doanh thu dựa trên dữ liệu thực tế của hệ thống, xác định món bán chạy và đưa ra các đề xuất hỗ trợ tăng doanh thu.

### Kiểm tra và chỉnh sửa

Sinh viên kiểm tra các số liệu do AI sử dụng bằng cách đối chiếu với dữ liệu trong cơ sở dữ liệu SQLite và điều chỉnh prompt khi cần thiết.

---

## 5. Công nghệ AI

Hệ thống sử dụng:

* Google Gemini API.
* Thư viện `google-genai`.
* Python Flask.
* SQLite.
* `python-dotenv` để đọc biến môi trường.

API Key được lưu trong file `.env` và không đưa trực tiếp vào mã nguồn.

---

## 6. Đánh giá việc sử dụng AI

AI được sử dụng như một công cụ hỗ trợ phân tích dữ liệu và ra quyết định.

Sinh viên không sử dụng kết quả AI một cách tuyệt đối mà thực hiện kiểm tra dữ liệu đầu vào, kiểm tra kết quả đầu ra và chỉnh sửa prompt/code khi cần thiết.

AI hỗ trợ phát triển các chức năng:

* Đề xuất thực đơn.
* Phân tích phản hồi.
* Phân tích doanh thu.
* Sinh nội dung báo cáo.
