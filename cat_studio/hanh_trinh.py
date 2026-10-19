# -*- coding: utf-8 -*-
"""HÀNH TRÌNH — 9 hồi, 26 màn, và màn nào mở ra cái gì.

Một chỗ DUY NHẤT biết trò chơi có những màn nào và chúng dạy gì. Giao diện không khai
lại một dòng: bản đồ hành trình chỉ hỏi ở đây rồi vẽ. Hai nơi cùng giữ danh sách màn thì
sớm muộn lệch nhau, mà cái lệch ấy chỉ lộ ra ở hồi ít người chơi tới nhất.

⚠ VÌ SAO 26 MÀN CHỨ KHÔNG PHẢI 164. App có 164 đại lượng, nhưng 90 trong số đó là CHỈ
BÁO — tức MỘT ý tưởng ("lấy một con số máy tính tính hộ từ giá") lặp lại 90 lần. Dạy
từng cái là 90 màn giống hệt nhau và người chơi bỏ ở màn thứ sáu. Nên luật là:

    Màn dạy NHÓM và NGỮ PHÁP. Kho dạy từng món.

9 nhóm đại lượng × "cách dùng nhóm này" + 4 thứ ngữ pháp vẽ + Cỗ máy + Optimize = 26
màn, phủ hết. Còn 164 món nằm trong màn hình KHO để tra, mở dần theo tiến trình.
Xem `tai_lieu/thiet_ke_tro_choi.md` §0 và §3.

⚠ CHƯA CÓ THỊ TRƯỜNG VÀ NGÀY THÁNG. Mỗi màn còn cần một mã + hai khoảng ngày (đã thấy /
ẩn) có thật và có chuyện để kể — chỗ ấy chủ dự án chọn, không phải tôi đoán. Mốc M1 chỉ
dựng BỘ KHUNG của hành trình; luật chơi và chấm sao là mốc M3 (chép từ `game.py` ở nhánh
`main`). Để trống còn hơn điền bừa rồi quên mất là mình bịa.

NHÃN Ở BẢNG HẰNG không bọc `tr()` được lúc nạp tệp — bọc là chốt cứng một thứ tiếng.
Dịch lúc DÙNG, trong `tu_dien()`. Xem `ngon_ngu.py`.
"""
import json
import os

from . import luu_tru
from .ngon_ngu import tr

FILE_SO = "hanh_trinh.json"

#: Chín hồi (cộng khúc dạo đầu). `ma` là khoá, đừng đổi — sổ tiến trình ghi theo nó.
HOI = (
    {"ma": "h0", "ten": "Khúc dạo đầu", "cau": "Một cái máy, hai khối"},
    {"ma": "h1", "ten": "Hỏi giá", "cau": "Máy phải biết nhìn"},
    {"ma": "h2", "ten": "Chỉ báo", "cau": "Đừng tự tính, bảo máy tính"},
    {"ma": "h3", "ten": "Vị thế & tài khoản", "cau": "Máy phải biết nó đang cầm gì"},
    {"ma": "h4", "ten": "Trí nhớ", "cau": "Máy phải nhớ được qua đêm"},
    {"ma": "h5", "ten": "Thời gian", "cau": "Lúc nào làm, lúc nào đứng im"},
    {"ma": "h6", "ten": "Nhiều mã", "cau": "Một cái máy, nhiều cần câu"},
    {"ma": "h7", "ten": "Doanh nghiệp", "cau": "Nhìn sổ sách, không chỉ nhìn giá"},
    {"ma": "h8", "ten": "Cỗ máy", "cau": "Cái máy chạy trên cái gì"},
    {"ma": "h9", "ten": "Hợp xưởng", "cau": "Nhiều máy trong một máy"},
)

#: 26 màn. `day` là MỘT ý mới duy nhất của màn ấy — và nó phải là thứ GIẢI ĐƯỢC màn đó,
#: không phải thứ đọc cho biết. `mo` là những gì màn ấy mở khoá.
#:
#: `dau` đánh dấu mấy màn gánh cả trò chơi (xem thiết kế §3) — bản đồ vẽ chúng khác đi.
MAN = (
    {"ma": "m00", "hoi": "h0", "ten": "Bạn chính là boss",
     "day": "Lắp máy hai khối: Bắt đầu → Đặt tỷ trọng 100%. Chạy thử. Nó CHÍNH LÀ "
            "«Mua rồi giữ» — con boss mà cả trò chơi phải đánh bại.",
     "mo": ("Khối Bắt đầu", "Đặt tỷ trọng", "Nút Chạy"), "dau": True},

    {"ma": "m01", "hoi": "h1", "ten": "Cái van đầu tiên",
     "day": "Chỉ mua khi giá trên một ngưỡng. Cổng Hỏi là cái van của cỗ máy.",
     "mo": ("Hỏi thị trường", "Nhóm Giá — 8 đại lượng")},
    {"ma": "m02", "hoi": "h1", "ten": "Vào thì phải có đường ra",
     "day": "Hai nhánh: một nhánh vào, một nhánh thoát.",
     "mo": ("Đóng", "Nhánh rẽ")},
    {"ma": "m03", "hoi": "h1", "ten": "Mã này có mua được không",
     "day": "Hỏi trạng thái mã trước khi đặt lệnh — sàn đóng cửa thì lệnh thành rác.",
     "mo": ("Nhóm Trạng thái mã — 5 đại lượng",)},

    {"ma": "m04", "hoi": "h2", "ten": "Mở kho",
     "day": "Chỉ báo đầu tiên (RSI) và tham số của nó. Đây là lúc KHO mở ra — "
            "90 chỉ báo, không phải để thuộc, mà để tra.",
     "mo": ("Nhóm Chỉ báo — 90 đại lượng", "Màn hình Kho")},
    {"ma": "m05", "hoi": "h2", "ten": "Chỉ báo nhiều đường",
     "day": "Bollinger, MACD — một chỉ báo trả về mấy đường, phải chọn đường nào.",
     "mo": ("Nhóm Chỉ báo nhiều đường — 16 đại lượng",)},
    {"ma": "m06", "hoi": "h2", "ten": "Và, hoặc",
     "day": "Ghép hai điều kiện trong một cổng.",
     "mo": ("Phép ghép và/hoặc",)},
    {"ma": "m07", "hoi": "h2", "ten": "Số nào là số tốt",
     "day": "Ghim một núm rồi quét hai mươi giá trị. Máy tự tìm hộ.",
     "mo": ("Optimize", "27 chỉ tiêu chấm")},
    {"ma": "m08", "hoi": "h2", "ten": "Màn ẩn vả cho một cái",
     "day": "Chạy lại đúng cỗ máy vừa ăn hai sao ở màn trước — trên khoảng ngày nó "
            "chưa từng thấy. Nó rụng xuống một sao. Bạn không làm chiến thuật, bạn "
            "vẽ lại quá khứ.",
     "mo": (), "dau": True},

    {"ma": "m09", "hoi": "h3", "ten": "Đang giữ rồi",
     "day": "Hỏi vị thế trước khi mua — không thì mỗi nến lại mua thêm một lần.",
     "mo": ("Hỏi vị thế", "Nhóm Vị thế — 12 đại lượng")},
    {"ma": "m10", "hoi": "h3", "ten": "Hết tiền",
     "day": "Hỏi tài khoản còn bao nhiêu trước khi đặt lệnh.",
     "mo": ("Hỏi tài khoản", "Nhóm Tài khoản — 8 đại lượng")},
    {"ma": "m11", "hoi": "h3", "ten": "Đặt lệnh nằm chờ",
     "day": "Lệnh chờ nằm trên sàn, khớp khi giá chạm. Và phải biết huỷ nó.",
     "mo": ("Lệnh chờ", "Huỷ lệnh chờ", "Lệnh thị trường")},

    {"ma": "m12", "hoi": "h4", "ten": "Nhớ qua đêm",
     "day": "Cất một quyết định lại cho nhịp sau đọc — «đang chờ mua lại». Đây là thứ "
            "làm cỗ máy thành một chương trình, không còn là một công thức.",
     "mo": ("Ghi nhớ", "Hỏi trí nhớ", "Nhóm Trí nhớ — 12 đại lượng")},
    {"ma": "m13", "hoi": "h4", "ten": "Vòng lặp",
     "day": "Khối Quay về — vẽ cái vòng ra, thay vì để nó ngầm.",
     "mo": ("Quay về", "Số vòng")},

    {"ma": "m14", "hoi": "h5", "ten": "Đúng giờ mới làm",
     "day": "Chỉ cân lại danh mục đầu tháng. Tránh phiên mở cửa.",
     "mo": ("Hỏi lịch", "Nhóm Thời gian — 6 đại lượng", "Nhịp chạy")},

    {"ma": "m15", "hoi": "h6", "ten": "Hai cần câu",
     "day": "Một cỗ máy chạy trên hai mã. Chạy cho từng mã, hay cho cả danh mục?",
     "mo": ("Ô «chạy cho ai»",)},
    {"ma": "m16", "hoi": "h6", "ten": "Cả một rổ",
     "day": "Thả cả rổ vào máy thay vì gõ tên từng mã.",
     "mo": ("6 rổ có sẵn",)},
    {"ma": "m17", "hoi": "h6", "ten": "Rổ tự lọc",
     "day": "Rổ không cố định — mỗi ngày máy tự chọn lại theo thanh khoản hay theo "
            "đường trung bình.",
     "mo": ("3 rổ lọc động",)},

    {"ma": "m18", "hoi": "h7", "ten": "Nhìn vào sổ sách",
     "day": "P/E, vốn hoá — hỏi về chính công ty, không hỏi về giá của nó.",
     "mo": ("Hỏi doanh nghiệp", "Nhóm Định giá — 7 đại lượng")},
    {"ma": "m19", "hoi": "h7", "ten": "Năm trăm công ty",
     "day": "Lọc trong rổ lớn, chia theo ngành.",
     "mo": ("Rổ QC500", "Rổ theo ngành S&P 500")},

    {"ma": "m20", "hoi": "h8", "ten": "Phí ăn hết lãi",
     "day": "Chạy lại đúng cỗ máy vừa ăn ba sao, chỉ bật phí sàn và trượt giá lên "
            "cho thật. Nó lỗ.",
     "mo": ("Sàn", "Phí", "Trượt giá"), "dau": True},
    {"ma": "m21", "hoi": "h8", "ten": "Giữ lại một ít",
     "day": "Đệm tiền mặt và phòng rủi ro — cỗ máy không được phép dốc sạch.",
     "mo": ("Đệm tiền mặt", "Phòng rủi ro", "Mốc so sánh")},
    {"ma": "m22", "hoi": "h8", "ten": "Để LEAN chia hộ",
     "day": "Thay vì tự đặt tỷ trọng, chỉ nói «mã này nên LÊN» rồi để LEAN lo chia "
            "vốn, phòng rủi ro và đặt lệnh.",
     "mo": ("Phát tín hiệu", "Chia vốn", "Đặt lệnh")},

    {"ma": "m23", "hoi": "h9", "ten": "Hai máy song song",
     "day": "Hai chiến thuật con chạy cùng lúc rồi trộn tỷ trọng.",
     "mo": ("Nhánh song song",)},
    {"ma": "m24", "hoi": "h9", "ten": "Gom lại thành một",
     "day": "Cả một cụm khối gói thành một Nhóm, nhìn lại thấy cái máy chứ không "
            "thấy mớ dây.",
     "mo": ("Nhóm", "Hạt nhân")},
    {"ma": "m25", "hoi": "h9", "ten": "Boss cuối",
     "day": "Thị trường xấu, và boss lần này không phải «Mua rồi giữ» — nó là một "
            "cỗ máy.",
     "mo": ("Chế độ Sáng tạo đầy đủ",), "dau": True},
)


def _so():
    """Sổ tiến trình. Hỏng hay chưa có thì coi như chưa chơi màn nào — KHÔNG ném:
    mất sổ chỉ nên làm mất tiến trình, không được chặn người ta vào trò chơi."""
    try:
        p = os.path.join(luu_tru.goc(), FILE_SO)
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _mo_toi_man(so):
    """Màn nào đang mở. -> set mã màn.

    LUẬT TẠM CỦA MỐC M1: mở màn đầu, và mở tiếp một màn sau mỗi màn đã xong. Luật thật
    (phải đủ sao mới qua) là mốc M3, lúc chép `game.py` từ nhánh `main` về — đừng viết
    luật chấm ở đây rồi mai có hai bản."""
    xong = {str(x) for x in (so.get("xong") or [])}
    mo = set()
    for m in MAN:
        mo.add(m["ma"])
        if m["ma"] not in xong:
            break
    return mo


def tu_dien():
    """Cả hành trình, đã dịch sẵn. -> {hoi: [...], man: [...], dang_o}

    Giao diện KHÔNG khai lại một màn nào — nó hỏi cửa này rồi vẽ. `mo` và `sao` đi kèm
    luôn, nên bản đồ không phải tự suy ra màn nào khoá."""
    so = _so()
    mo = _mo_toi_man(so)
    sao = so.get("sao") or {}
    xong = {str(x) for x in (so.get("xong") or [])}
    return {
        "hoi": [{"ma": h["ma"], "ten": tr(h["ten"]), "cau": tr(h["cau"])} for h in HOI],
        "man": [{
            "ma": m["ma"],
            "hoi": m["hoi"],
            "so": i,
            "ten": tr(m["ten"]),
            "day": tr(m["day"]),
            "mo": [tr(x) for x in m["mo"]],
            "dau": bool(m.get("dau")),
            "khoa": m["ma"] not in mo,
            "xong": m["ma"] in xong,
            "sao": int(sao.get(m["ma"]) or 0),
        } for i, m in enumerate(MAN)],
        # Màn người chơi đang đứng: màn mở mới nhất chưa xong.
        "dang_o": next((m["ma"] for m in MAN
                        if m["ma"] in mo and m["ma"] not in xong), MAN[-1]["ma"]),
        # ⚠ Nói thẳng ra là luật chấm CHƯA có, để giao diện đừng vẽ sao như thật.
        "co_luat_cham": False,
    }
