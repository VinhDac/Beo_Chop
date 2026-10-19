# -*- coding: utf-8 -*-
"""BẢNG DỊCH TIẾNG ANH của chữ do PYTHON sinh ra: câu tiếng Việt → câu tiếng Anh. Xem `ngon_ngu.py`.

KHOÁ là câu tiếng Việt đúng từng chữ như trong mã, bỏ khoảng trắng hai đầu. Không phải gõ tay:
`tools\\dich.bat` tự thêm câu còn thiếu vào đúng nhóm tệp, giá trị để trống — chỉ việc điền bản
tiếng Anh. Câu trong mã đổi thì khoá cũ thành thừa — `tools\\dich.bat --don` bỏ đi. MỖI CÂU MỘT
DÒNG, dài cũng để một dòng: công cụ thêm / bỏ theo dòng.

Ô điền (`{0}`, `{1:.1f}`, `%d`…) hai bên phải khớp nhau. Bản tiếng Anh được dùng `{0|one|other}`
cho số ít / số nhiều. Viết hoa, chấm câu theo đúng câu gốc: câu gốc viết thường (dòng nhật ký,
lý do) thì bản Anh cũng viết thường.

THUẬT NGỮ: một bảng cho cả app, ở đầu `webui/src/tieng_anh.ts` — đừng chép sang đây. Câu nào có
ở CẢ HAI bảng (nhãn Python mà web cũng hiện) thì hai bản tiếng Anh phải giống hệt; công cụ soát.
"""

TIENG_ANH = {
}
