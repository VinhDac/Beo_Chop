"""Khung cửa sổ RỖNG — đứng thay `khung_cua_so` khi không chạy trên Windows.

Chỉ để `api.py` nạp được trong bài kiểm trên Linux/CI. Mọi thao tác là không làm gì;
`tim_hwnd` không bao giờ tìm thấy cửa sổ nào. App thật chỉ chạy trên Windows.
"""


def tim_hwnd(chua_chuoi):
    return None


class KhungTuVe:
    def dat_vung_cam(self, vung, cao):
        pass

    def bat_dau_keo(self, ht):
        return False

    def phong_to_hay_khoi_phuc(self, win):
        pass

    def dang_phong_to(self):
        return False

    def keo_len_truoc(self):
        pass

    def dang_hien(self):
        return False

    def va(self, hwnd):
        return False
