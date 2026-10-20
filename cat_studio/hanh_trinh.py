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
from .ngon_ngu import tr

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

#: ⚠ `an_mo_ta` TẢ BẰNG LỜI MƠ HỒ, CÓ CHỦ Ý. Bản đầu viết "12 tháng ngay sau màn đã
#: thấy" — nghe thì tử tế, nhưng cộng với khoảng ngày ĐÃ THẤY (vốn bày công khai) là
#: người chơi TÍNH RA được khoảng ẩn, rồi sang Sáng tạo chạy thử đúng khoảng ấy mà vặn
#: máy cho khít. Ngôi sao thứ ba mất sạch nghĩa mà vẫn sáng lên y như thật.
#:
#: 26 màn. `day` là MỘT ý mới duy nhất của màn ấy — và nó phải là thứ GIẢI ĐƯỢC màn đó,
#: không phải thứ đọc cho biết. `mo` là những gì màn ấy mở khoá.
#:
#: `dau` đánh dấu mấy màn gánh cả trò chơi (xem thiết kế §3) — bản đồ vẽ chúng khác đi.
MAN = (
    {"ma": "m00", "hoi": "h0", "ten": "Bạn chính là boss",
     "day": "Lắp máy hai khối: Bắt đầu → Đặt tỷ trọng 100%. Chạy thử. Nó CHÍNH LÀ "
            "«Mua rồi giữ» — con boss mà cả trò chơi phải đánh bại.",
     "mo": ('khoi:bat_dau', 'lam:lam_dat_ty_trong', 'nut:chay'), "dau": True,
     # ⚠ MÀN NÀY KHÔNG CHẤM, và đó là hệ quả bắt buộc của luật sao chứ không phải
     # lười. ⭐ đòi ÍT NHẤT MỘT LỆNH ĐÓNG (xem `luat_choi`), mà màn này bảo người
     # chơi dựng đúng «Mua rồi giữ» — thứ không đóng lệnh nào. Chấm nó là bắt người
     # chơi nhìn 0 sao ngay màn đầu tiên vì đã làm ĐÚNG lời dặn.
     "khong_cham": True,
     "symbol": "SPY", "loai_ma": "equity", "von": 100_000.0,
     "thay": ("2013-01-01", "2013-12-31"),
     "loi_dan": "Năm 2013 chứng khoán Mỹ lên gần như một mạch. Lắp cái máy đơn giản "
                "nhất có thể rồi bấm chạy — để thấy con số mà cả hành trình này phải "
                "vượt qua trông như thế nào."},

    {"ma": "m01", "hoi": "h1", "ten": "Cái van đầu tiên",
     "day": "Chỉ mua khi giá trên một ngưỡng. Cổng Hỏi là cái van của cỗ máy.",
     "mo": ('ho:hoi_thi_truong', 'nhom:Giá'),
     "symbol": "XAUUSD", "loai_ma": "cfd", "von": 100_000.0,
     "thay": ("2012-01-01", "2014-12-31"), "an": ("2015-01-01", "2015-12-31"),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 3,
     "loi_dan": "Ba năm vàng đi xuống. Mua rồi giữ là lỗ — nên lần này boss YẾU, và "
                "thứ đánh bại nó không phải là giỏi mua, mà là biết lúc nào đứng "
                "ngoài."},

    {"ma": "m02", "hoi": "h1", "ten": "Vào thì phải có đường ra",
     "day": "Hai nhánh: một nhánh vào, một nhánh thoát.",
     "mo": ('lam:lam_dong', 'ngu_phap:nhanh'),
     "symbol": "SPY", "loai_ma": "equity", "von": 100_000.0,
     "thay": ("2007-01-01", "2009-12-31"), "an": ("2010-01-01", "2010-12-31"),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": "2008. Ai mua rồi giữ thì mất gần một nửa rồi ngồi chờ lấy lại. Màn "
                "này dạy đúng một chuyện: cái máy phải có đường RA, không chỉ có "
                "đường vào."},

    {"ma": "m03", "hoi": "h1", "ten": "Ngày mã chia tách",
     "day": "Ngày 09/06/2014 Apple chia tách 7 ăn 1: giá rơi từ 645 xuống 92 chỉ sau "
            "một đêm, mà công ty không hề mất gì. Cỗ máy nhìn giá mà không hỏi hôm "
            "nay có chia tách không thì tưởng trời sập.",
     "mo": ('nhom:Trạng thái mã',),
     "symbol": "AAPL", "loai_ma": "equity", "von": 100_000.0,
     "thay": ("2014-01-01", "2014-12-31"), "an": ("2015-01-01", "2015-12-31"),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": "Apple năm 2014, có đúng một ngày chia tách nằm giữa. Boss khoẻ — "
                "mua rồi giữ năm ấy lãi đậm. Muốn hơn nó thì phải vào đúng nhịp, mà "
                "muốn vào đúng nhịp thì trước hết đừng để cái ngày 09/06 lừa."},

    {"ma": "m04", "hoi": "h2", "ten": "Mở kho",
     "day": "Chỉ báo đầu tiên (RSI) và tham số của nó. Đây là lúc KHO mở ra — "
            "90 chỉ báo, không phải để thuộc, mà để tra.",
     "mo": ('nhom:Chỉ báo', 'man:kho'),
     "symbol": 'SPY', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2015-01-01', '2017-12-31'), "an": ('2018-01-01', '2018-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 4,
     "loi_dan": 'Ba năm thị trường đi ngang rồi lên chậm — kiểu thị trường mà chỉ báo quá bán / quá mua ăn tiền. Màn ẩn là 2018, năm có hai cú sụt mạnh: đủ để biết cái máy có thật sự hiểu gì không.'},
    {"ma": "m05", "hoi": "h2", "ten": "Chỉ báo nhiều đường",
     "day": "Bollinger, MACD — một chỉ báo trả về mấy đường, phải chọn đường nào.",
     "mo": ('nhom:Chỉ báo nhiều đường',),
     "symbol": 'XAUUSD', "loai_ma": 'cfd', "von": 100_000.0,
     "thay": ('2015-01-01', '2017-12-31'), "an": ('2018-01-01', '2018-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'Vàng đáy 2015 rồi bò lên. Một chỉ báo trả về mấy đường — dải Bollinger chẳng hạn — nói được cả xu hướng lẫn độ rộng, thứ mà một đường đơn không nói nổi.'},
    {"ma": "m06", "hoi": "h2", "ten": "Và, hoặc",
     "day": "Ghép hai điều kiện trong một cổng.",
     "mo": ('ngu_phap:ghep',),
     "symbol": 'AAPL', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Apple ba năm lên mạnh, boss KHOẺ. Một điều kiện không đủ để hơn nó — phải ghép hai cái lại mới lọc ra đúng nhịp.'},
    {"ma": "m07", "hoi": "h2", "ten": "Số nào là số tốt",
     "day": "Ghim một núm rồi quét hai mươi giá trị. Máy tự tìm hộ.",
     "mo": ('tinh_nang:toi_uu',),
     "symbol": 'IBM', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2013-01-01', '2016-12-31'), "an": ('2017-01-01', '2017-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'IBM bốn năm đi xuống — boss yếu, nên bạn rảnh tay nghịch. Ghim một núm rồi để máy quét hai mươi giá trị, xem con số nào hợp.'},
    {"ma": "m08", "hoi": "h2", "ten": "Màn ẩn vả cho một cái",
     "day": "Chạy lại đúng cỗ máy vừa ăn hai sao ở màn trước — trên khoảng ngày nó "
            "chưa từng thấy. Nó rụng xuống một sao. Bạn không làm chiến thuật, bạn "
            "vẽ lại quá khứ.",
     "mo": (), "dau": True,
     "symbol": 'AAPL', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2018-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 4,
     "loi_dan": 'Hai năm Apple lên đẹp, vặn núm cho khít là ăn ngay hai sao. Rồi nộp. Màn ẩn là 2020 — năm thị trường rơi một phần ba trong năm tuần rồi dựng lại. Cỗ máy khít 2019 sống qua được không?'},

    {"ma": "m09", "hoi": "h3", "ten": "Đang giữ rồi",
     "day": "Hỏi vị thế trước khi mua — không thì mỗi nến lại mua thêm một lần.",
     "mo": ('ho:hoi_vi_the', 'nhom:Vị thế'),
     "symbol": 'AAPL', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2017-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'Máy chưa biết hỏi «đang giữ chưa» thì mỗi nến lại mua thêm một lần, và hết tiền từ tháng thứ hai.'},
    {"ma": "m10", "hoi": "h3", "ten": "Hết tiền",
     "day": "Hỏi tài khoản còn bao nhiêu trước khi đặt lệnh.",
     "mo": ('ho:hoi_tai_khoan', 'nhom:Tài khoản'),
     "symbol": 'BAC', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'Ngân hàng Mỹ ba năm lên rồi chững. Đặt lệnh khi tài khoản không còn tiền thì sàn từ chối — mà lệnh bị từ chối vẫn là một dòng trong nhật ký, không phải một cái máy đang chạy tốt.'},
    {"ma": "m11", "hoi": "h3", "ten": "Đặt lệnh nằm chờ",
     "day": "Lệnh chờ nằm trên sàn, khớp khi giá chạm. Và phải biết huỷ nó.",
     "mo": ('lam:lam_lenh_cho', 'lam:lam_huy_lenh_cho', 'lam:lam_lenh_thi_truong'),
     "symbol": 'XAUUSD', "loai_ma": 'cfd', "von": 100_000.0,
     "thay": ('2009-01-01', '2011-12-31'), "an": ('2012-01-01', '2012-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Ba năm vàng lên dữ nhất lịch sử rồi lập đỉnh 2011. Lệnh chờ đặt sẵn ở giá mình muốn thay vì đuổi theo giá — và phải biết huỷ nó khi tình thế đổi.'},

    {"ma": "m12", "hoi": "h4", "ten": "Nhớ qua đêm",
     "day": "Cất một quyết định lại cho nhịp sau đọc — «đang chờ mua lại». Đây là thứ "
            "làm cỗ máy thành một chương trình, không còn là một công thức.",
     "mo": ('lam:lam_ghi_nho', 'ho:hoi_tri_nho', 'nhom:Trí nhớ'),
     "symbol": 'SPY', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2017-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": '«Vừa bán xong, chờ giá về rồi mua lại» — câu ấy cần TRÍ NHỚ. Trong một nến thì không có gì để nhớ; qua nến mới cần.'},
    {"ma": "m13", "hoi": "h4", "ten": "Vòng lặp",
     "day": "Khối Quay về — vẽ cái vòng ra, thay vì để nó ngầm.",
     "mo": ('khoi:quay_ve',),
     "symbol": 'XAUUSD', "loai_ma": 'cfd', "von": 100_000.0,
     "thay": ('2006-04-01', '2008-12-31'), "an": ('2009-01-01', '2009-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Vàng qua khủng hoảng 2008 — rơi cùng mọi thứ rồi bật lại trước mọi thứ. Vẽ cái vòng lặp ra thay vì để nó ngầm.'},

    {"ma": "m14", "hoi": "h5", "ten": "Đúng giờ mới làm",
     "day": "Chỉ cân lại danh mục đầu tháng. Tránh phiên mở cửa.",
     "mo": ('ho:hoi_lich', 'nhom:Thời gian', 'o:nhip'),
     "symbol": 'SPY', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'Cân lại danh mục mỗi ngày thì phí ăn hết; mỗi tháng một lần thì vừa. Và phiên mở cửa là chỗ giá nhảy loạn nhất ngày.'},

    {"ma": "m15", "hoi": "h6", "ten": "Hai cần câu",
     "day": "Một cỗ máy chạy trên hai mã. Chạy cho từng mã, hay cho cả danh mục?",
     "mo": ('o:chay_cho',),
     "symbol": ('SPY', 'QQQ'), "loai_ma": 'equity', "von": 100_000.0,
     "moc": 'SPY',
     "thay": ('2017-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Hai mã cùng chạy một cỗ máy. Boss là mua-giữ SPY. Chạy cho TỪNG mã hay cho CẢ danh mục — hai câu trả lời, hai cỗ máy khác hẳn nhau.'},
    {"ma": "m16", "hoi": "h6", "ten": "Cả một rổ",
     "day": "Thả cả rổ vào máy thay vì gõ tên từng mã.",
     "mo": ('ro:co_san',),
     "ro": 'nang_luong',
     "symbol": ('USO',), "loai_ma": 'equity', "von": 100_000.0,
     "moc": 'SPY',
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Thả cả rổ ETF năng lượng vào máy thay vì gõ tên từng mã. Dữ liệu trên máy này chỉ đỡ được hai mã trong rổ (USO, BNO) — rổ vẫn chạy, chỉ là mỏng. Boss lần này là mua-giữ SPY, tức cả thị trường — khó hơn hẳn, nhưng đó mới là câu hỏi thật: chọn riêng một ngành có hơn được việc mua cả chợ không?'},
    {"ma": "m17", "hoi": "h6", "ten": "Rổ tự lọc",
     "day": "Rổ không cố định — mỗi ngày máy tự chọn lại theo thanh khoản hay theo "
            "đường trung bình.",
     "mo": ('ro:dong',),
     "vi_sao_chua": 'Ba rổ tự lọc (thanh khoản, cắt EMA) đều cần DỮ LIỆU DOANH NGHIỆP — hàng trả tiền của QuantConnect. Với dữ liệu miễn phí, `has_fundamental_data` trả False cho cả 7.111 mã nên rổ chọn ra số không.'},

    {"ma": "m18", "hoi": "h7", "ten": "Nhìn vào sổ sách",
     "day": "P/E, vốn hoá — hỏi về chính công ty, không hỏi về giá của nó.",
     "mo": ('ho:hoi_doanh_nghiep', 'nhom:Định giá'),
     "vi_sao_chua": 'Hỏi doanh nghiệp (P/E, vốn hoá) đọc kho `fine` của QuantConnect — hàng trả tiền. Không có nó thì mọi điều kiện đều rỗng.'},
    {"ma": "m19", "hoi": "h7", "ten": "Năm trăm công ty",
     "day": "Lọc trong rổ lớn, chia theo ngành.",
     "mo": ('ro:qc500',),
     "vi_sao_chua": 'Rổ QC500 và rổ theo ngành S&P 500 cũng cần kho `fine`, và dữ liệu trên máy không có mã nào của rổ ngành.'},

    {"ma": "m20", "hoi": "h8", "ten": "Phí ăn hết lãi",
     "day": "Chạy lại đúng cỗ máy vừa ăn ba sao, chỉ bật phí sàn và trượt giá lên "
            "cho thật. Nó lỗ.",
     "mo": ('o_may:san', 'o_may:phi', 'o_may:truot_gia'), "dau": True,
     "symbol": 'AAPL', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2015-01-01', '2017-12-31'), "an": ('2018-01-01', '2018-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 5,
     "loi_dan": 'Lấy đúng cỗ máy bạn tâm đắc nhất, rồi bật phí sàn và trượt giá lên cho THẬT. Nếu nó vẫn sống thì mới là nó sống.'},
    {"ma": "m21", "hoi": "h8", "ten": "Giữ lại một ít",
     "day": "Đệm tiền mặt và phòng rủi ro — cỗ máy không được phép dốc sạch.",
     "mo": ('o_may:dem_tien_mat', 'o_may:phong_rui_ro', 'o_may:moc_so_sanh'),
     "symbol": 'AIG', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2017-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'AIG — cổ phiếu từng suýt kéo sập cả hệ thống, và vẫn còn nảy rất mạnh. Máy dốc sạch tiền vào một cú là sớm muộn gặp đúng cú sai.'},
    {"ma": "m22", "hoi": "h8", "ten": "Để LEAN chia hộ",
     "day": "Thay vì tự đặt tỷ trọng, chỉ nói «mã này nên LÊN» rồi để LEAN lo chia "
            "vốn, phòng rủi ro và đặt lệnh.",
     "mo": ('lam:lam_tin_hieu', 'o_may:chia_von', 'o_may:dat_lenh'),
     "symbol": ('SPY', 'QQQ', 'IWM'), "loai_ma": 'equity', "von": 100_000.0,
     "moc": 'SPY',
     "thay": ('2017-01-01', '2019-12-31'), "an": ('2020-01-01', '2020-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 6,
     "loi_dan": 'Thôi tự đặt tỷ trọng. Chỉ nói «mã này nên LÊN» rồi để LEAN lo chia vốn, chặn rủi ro và đặt lệnh — đúng dây chuyền thật của nó.'},

    {"ma": "m23", "hoi": "h9", "ten": "Hai máy song song",
     "day": "Hai chiến thuật con chạy cùng lúc rồi trộn tỷ trọng.",
     "mo": ('ngu_phap:song_song',),
     "symbol": ('SPY', 'QQQ'), "loai_ma": 'equity', "von": 100_000.0,
     "moc": 'SPY',
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 8,
     "loi_dan": 'Hai chiến thuật con chạy cùng lúc rồi trộn tỷ trọng. Hai cái nửa vời cộng lại có khi hơn một cái giỏi.'},
    {"ma": "m24", "hoi": "h9", "ten": "Gom lại thành một",
     "day": "Cả một cụm khối gói thành một Nhóm, nhìn lại thấy cái máy chứ không "
            "thấy mớ dây.",
     "mo": ('khoi:nhom', 'khoi:hat_nhan'),
     "symbol": 'AAPL', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2016-01-01', '2018-12-31'), "an": ('2019-01-01', '2019-12-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 8,
     "loi_dan": 'Sơ đồ tới đây đã rậm. Gói cả cụm thành một Nhóm để nhìn lại thấy CÁI MÁY, chứ không thấy mớ dây.'},
    {"ma": "m25", "hoi": "h9", "ten": "Boss cuối",
     "day": "Thị trường xấu, và boss lần này không phải «Mua rồi giữ» — nó là một "
            "cỗ máy.",
     "mo": ('che_do:sang_tao',), "dau": True,
     "symbol": 'SPY', "loai_ma": 'equity', "von": 100_000.0,
     "thay": ('2018-01-01', '2020-12-31'), "an": ('2021-01-01', '2021-03-31'),
     "an_mo_ta": "một khoảng ngày cỗ máy chưa từng thấy", "boss": "mua_giu", "gon": 8,
     "loi_dan": 'Ba năm có đủ mọi thứ: sụt cuối 2018, sập 2020, rồi dựng lại dữ dội. Boss vẫn là mua-giữ, và lần này nó rất khoẻ. Mang hết những gì đã học ra.'},
)


def _mo_toi_man(xong):
    """Màn nào đang mở. -> set mã màn.

    Mở màn đầu, rồi mở tiếp một màn sau mỗi màn ĐÃ XONG. "Xong" = đã chạy được một
    lượt sạch (hoặc là màn không chấm) — không đòi phải đủ ba sao: bắt ăn ba sao mới
    đi tiếp là giam người chơi ở màn đầu, mà ngôi sao thứ ba cố ý khó.

    ⚠ `xong` ĐẾN TỪ SỔ ĐIỂM, không từ một sổ riêng. Bản trước có HAI sổ — `tu_dien`
    đọc sổ điểm còn hàm này đọc `hanh_trinh.json` — nên chơi xong một màn thì sổ điểm
    ghi nhận mà bản đồ vẫn khoá màn kế, mãi mãi. Hai nơi cùng giữ một sự thật, đúng
    cái bệnh dự án này đã dính nhiều lần."""
    mo = set()
    for m in MAN:
        mo.add(m["ma"])
        if m["ma"] not in xong:
            break
    return mo


#: Nhãn cho mấy khoá không thuộc từ điển nào (nút, khối, ngữ pháp, chế độ).
#: Chỉ những thứ KHÔNG có chỗ nào khác khai — còn lại đều tra từ điển.
NHAN_KHAC = {
    "khoi:bat_dau": "Khối Bắt đầu",
    "khoi:quay_ve": "Khối Quay về",
    "khoi:nhom": "Khối Nhóm",
    "khoi:hat_nhan": "Hạt nhân",
    "nut:chay": "Nút Chạy",
    "ngu_phap:nhanh": "Nhánh rẽ",
    "ngu_phap:ghep": "Phép ghép và/hoặc",
    "ngu_phap:song_song": "Nhánh song song",
    "tinh_nang:toi_uu": "Optimize",
    "man:kho": "Màn hình Kho",
    "che_do:sang_tao": "Chế độ Sáng tạo đầy đủ",
    "o:nhip": "Ô «Nhịp»",
    "o:chay_cho": "Ô «Chạy cho ai»",
    "ro:co_san": "Mấy rổ có sẵn",
    "ro:dong": "Rổ tự lọc",
    "ro:qc500": "Rổ QC500 và rổ theo ngành",
}


def nhan_mo(khoa):
    """Một khoá mở -> chữ bày cho người chơi. -> str

    ⚠ DỰNG TỪ TỪ ĐIỂN THẬT, không gõ sẵn. Bản đầu viết tay "Nhóm Giá — 8 đại lượng"
    vào từng màn: một con số chép tay, nằm cách chỗ sinh ra nó ba tệp. Thêm một đại
    lượng vào nhóm Giá là câu ấy thành sai, mà không có gì kêu — và nó sai ở đúng chỗ
    người chơi đang học đếm."""
    from . import hoi, lam
    loai, _, gt = str(khoa).partition(":")
    if loai == "nhom":
        n = sum(1 for m in hoi.tu_dien()["kho"] if m.get("nhom") == gt)
        return tr("Nhóm {0} — {1} đại lượng", tr(gt), n)
    # ⚠ `tr()` cả nhãn từ điển. Chúng là hằng bên Python nên không bọc được lúc
    # nạp tệp; ở những chỗ nhãn đi NGUYÊN sang giao diện thì chính giao diện dịch,
    # nhưng ở đây Python đã GHÉP nó vào một câu rồi — nên phải dịch tại chỗ, không
    # thì vỏ tiếng Anh mà mấy thẻ mở khoá vẫn tiếng Việt.
    if loai == "ho":
        for h in hoi.tu_dien()["loai"]:
            if h["ma"] == gt:
                return tr(h["nhan"])
        return gt
    if loai == "lam":
        for x in lam.tu_dien()["loai"]:
            if x["ma"] == gt:
                return tr(x["nhan"])
        return gt
    if loai == "o_may":
        from . import bat_dau
        for o in bat_dau.o_co_may():
            if o["ten"] == gt:
                return tr(o["nhan"])
        return gt
    return tr(NHAN_KHAC.get(khoa, khoa))


def da_mo(sao):
    """Những khoá người chơi ĐÃ MỞ. -> set

    Mở theo MÀN ĐÃ TỚI, không theo màn đã ăn sao: vào được màn nào thì có đủ đồ nghề
    giải màn ấy. Bắt phải ăn sao mới mở đồ của chính màn đang chơi là khoá người ta
    bên ngoài căn phòng họ đang đứng."""
    ra = set()
    xong = {k for k, v in (sao or {}).items() if v}
    for m in MAN:
        ra |= set(m.get("mo") or ())
        if m["ma"] not in xong:
            break
    return ra


def man(ma):
    """Một màn theo mã. -> dict đầy đủ (CÓ ngày màn ẩn) hay None.

    ⚠ Bản ĐẦY ĐỦ chỉ dùng trong Python. Thứ đi ra giao diện phải qua `cong_khai`."""
    for m in MAN:
        if m["ma"] == str(ma):
            return m
    return None


def co_san(m):
    """Màn này đã có sân chơi thật chưa (mã + khoảng ngày).

    26 màn đã khai đủ BỘ KHUNG, nhưng mỗi màn còn cần một mã và hai khoảng ngày có
    thật, có chuyện để kể — chỗ ấy làm dần. Màn chưa có sân thì vào Xưởng vẽ được,
    chỉ chưa chạy chấm được, và bản đồ phải NÓI RA chứ đừng để người chơi bấm vào
    rồi mới thấy không có gì."""
    return bool((m or {}).get("symbol") and (m or {}).get("thay"))


def cong_khai(m):
    """Một màn -> phần giao diện được biết. KHÔNG có ngày của màn ẩn.

    ⚠ ĐÂY LÀ CẢ TRÒ CHƠI, không phải chuyện giấu cho vui. Ngôi sao thứ ba nói "cỗ máy
    này còn chạy được trên khoảng ngày nó chưa từng thấy". Người chơi biết ngày màn ẩn
    là vặn được máy cho vừa khít chính khoảng ấy, và ngôi sao thứ ba mất sạch nghĩa —
    mà mất nghĩa thì không ai biết, vì nó vẫn sáng lên y như thật."""
    from . import luat_choi
    if not co_san(m):
        # NÓI VÌ SAO, đừng chỉ nói "chưa có". Ba màn thiếu sân vì DỮ LIỆU MIỄN PHÍ của
        # LEAN không đỡ nổi, không phải vì chưa ai làm — mà hai chuyện ấy dẫn tới hai
        # hành động khác hẳn nhau cho người đọc.
        return {"co_san": False, "vi_sao_chua": tr(m.get("vi_sao_chua") or "")}
    return {
        "co_san": True,
        "symbol": m["symbol"],
        "von": m["von"],
        "thay": list(m["thay"]),
        "an_mo_ta": tr(m.get("an_mo_ta") or ""),
        "co_man_an": bool(m.get("an")),
        "khong_cham": bool(m.get("khong_cham")),
        "gon": m.get("gon"),
        "loi_dan": tr(m.get("loi_dan") or ""),
        "boss": luat_choi.ten_boss(m["boss"]) if m.get("boss") else None,
    }


def tu_dien():
    """Cả hành trình, đã dịch sẵn. -> {hoi: [...], man: [...], dang_o}

    Giao diện KHÔNG khai lại một màn nào — nó hỏi cửa này rồi vẽ. `mo` và `sao` đi kèm
    luôn, nên bản đồ không phải tự suy ra màn nào khoá."""
    from . import luat_choi
    # MỘT SỔ DUY NHẤT: sổ điểm. Sao, "đã xong", và cả chuyện mở khoá đều đọc từ đây.
    diem = luat_choi.doc_so()["man"]
    sao = {k: int((v or {}).get("sao") or 0) for k, v in diem.items()}
    # XONG = đã chạy được một lượt (có phần chấm `thay`), hay là màn không chấm mà
    # người chơi đã chạy qua. Không đòi sao: xem `_mo_toi_man`.
    xong = {k for k, v in diem.items() if (v or {}).get("thay") or v.get("sao")}
    mo = _mo_toi_man(xong)
    return {
        "hoi": [{"ma": h["ma"], "ten": tr(h["ten"]), "cau": tr(h["cau"])} for h in HOI],
        "man": [{
            "ma": m["ma"],
            "hoi": m["hoi"],
            "so": i,
            "ten": tr(m["ten"]),
            "day": tr(m["day"]),
            "mo": [nhan_mo(x) for x in m["mo"]],
            "dau": bool(m.get("dau")),
            "khoa": m["ma"] not in mo,
            "xong": m["ma"] in xong,
            "sao": int(sao.get(m["ma"]) or 0),
            **cong_khai(m),
        } for i, m in enumerate(MAN)],
        # Màn người chơi đang đứng: màn mở mới nhất chưa xong.
        "dang_o": next((m["ma"] for m in MAN
                        if m["ma"] in mo and m["ma"] not in xong), MAN[-1]["ma"]),
        # ⚠ Nói thẳng ra là luật chấm CHƯA có, để giao diện đừng vẽ sao như thật.
        "co_luat_cham": False,
    }
