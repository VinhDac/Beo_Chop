import { useCallback, useEffect, useRef, useState } from 'react'
import { py, pyGame } from '../api'
import type {
  BootGame, DongNkQC, KetQuaQC, LoaiChay, LoiTruyen, LuotGame, ManGame, PhieuMan, ProcessDoc,
  Problem, SoiLuot, TrangThaiQC,
} from '../types'

/** NÃO CỦA GAME phía giao diện — màn hình nào đang mở, màn nào, lượt nào, phát lại tới đâu.
 *
 * Luật KHÔNG nằm ở đây: sao, boss, vé nộp, màn mở/khoá đều do Python trả (`game.py`). Hook
 * này chỉ giữ trạng thái màn hình và gọi `pyGame.*`. Trình vẽ sơ đồ (App) cho nó bốn cái
 * cầu: lấy sơ đồ đang vẽ, nạp sơ đồ, tô một lượt, ghi nhật ký.
 *
 * Luồng (khuôn Opus Magnum — DECISIONS.md D-09):
 *   chinh → chon_man → (truyen) → phieu → XƯỞNG (sơ đồ) ⇄ chạy → ket_qua → xem máy nghĩ
 *                                              └→ nop (màn ẩn) → hoan_thanh → chon_man
 */
export type ManHinh = 'chinh' | 'chon_man' | 'truyen' | 'phieu' | 'xuong' | 'ket_qua' | 'nop'
  | 'hoan_thanh'

export interface CauNoiXuong {
  laySoDo: () => ProcessDoc
  napSoDo: (doc: ProcessDoc, loi: string) => void
  soi: (d: SoiLuot | null) => void
  ghi: (m: string, tag?: string | null) => void
}

export interface TruyenDangXem {
  chuong: string; phan: 'mo' | 'dong'; loi: LoiTruyen[]; k: number; sau: ManHinh
}

/** Phát lại: danh sách lượt (trang đã tải), vị trí, đang chạy hay dừng, tốc độ. */
export interface PhatLai {
  ds: DongNkQC[]
  tong: number
  k: number
  phat: boolean
  toc: number
  chiViec: boolean
  chu: string
  /** Bản soi của lượt đang xem — đường đi, cổng nào qua / trượt (cho bong bóng "máy nghĩ"). */
  luot: LuotGame | null
}

export interface HoanThanhMan {
  man: ManGame
  sao: number
  lanNop: number
  manTiep: ManGame | null
  xongChuong: boolean
}

const NHIP_HOI = 300
const LO_PHAT = 2000

export function useGame(cn: CauNoiXuong) {
  const [bat, setBat] = useState(false)
  const [manHinh, setManHinh] = useState<ManHinh>('chinh')
  const [boot, setBoot] = useState<BootGame | null>(null)
  const [chuongId, setChuongId] = useState('c1')
  const [manId, setManId] = useState<string | null>(null)
  const [phieu, setPhieu] = useState<PhieuMan | null>(null)
  const [truyen, setTruyen] = useState<TruyenDangXem | null>(null)
  const [tt, setTt] = useState<TrangThaiQC | null>(null)
  const [loi, setLoi] = useState('')
  const [kq, setKq] = useState<KetQuaQC | null>(null)
  const [nop, setNop] = useState<KetQuaQC | null>(null)
  const [phat, setPhat] = useState<PhatLai | null>(null)
  const [hoanThanh, setHoanThanh] = useState<HoanThanhMan | null>(null)
  const cnRef = useRef(cn)
  cnRef.current = cn
  const dangHoi = useRef(false)

  const tatCaMan = boot?.chuong.flatMap(c => c.man) ?? []
  const man = tatCaMan.find(m => m.id === manId) ?? null

  /* ------------------------------ nạp ------------------------------ */
  const napBoot = useCallback(async () => {
    const r = await pyGame.boot()
    if (r.ok && r.value) {
      setBoot(r.value)
      if (r.value.trang_thai?.dang_chay) setTt(r.value.trang_thai)
      return r.value
    }
    setLoi(r.error ?? 'không nạp được game')
    return null
  }, [])

  const napPhieu = useCallback(async (id: string) => {
    const r = await pyGame.man(id, cnRef.current.laySoDo())
    if (r.ok && r.value) setPhieu(r.value)
    return r.ok ? r.value ?? null : null
  }, [])

  /* ------------------------------ điều hướng ------------------------------ */
  const moGame = useCallback(async () => {
    setBat(true)
    setManHinh('chinh')
    setLoi('')
    await napBoot()
  }, [napBoot])

  const thoatGame = useCallback(() => {
    setBat(false)
    setPhat(null)
    cnRef.current.soi(null)
  }, [])

  const xemTruyen = useCallback(async (chuong: string, phan: 'mo' | 'dong', sau: ManHinh) => {
    const r = await pyGame.truyen(chuong, phan)
    if (!r.ok || !r.value || !r.value.loi.length) { setManHinh(sau); return }
    setTruyen({ chuong, phan, loi: r.value.loi, k: 0, sau })
    setManHinh('truyen')
  }, [])

  const truyenTiep = useCallback(async () => {
    if (!truyen) return
    if (truyen.k + 1 < truyen.loi.length) { setTruyen({ ...truyen, k: truyen.k + 1 }); return }
    await pyGame.daXemTruyen(truyen.chuong, truyen.phan)
    setManHinh(truyen.sau)
    setTruyen(null)
  }, [truyen])

  const boQuaTruyen = useCallback(async () => {
    if (!truyen) return
    await pyGame.daXemTruyen(truyen.chuong, truyen.phan)
    setManHinh(truyen.sau)
    setTruyen(null)
  }, [truyen])

  /** Vào chiến dịch: lần đầu vào chương thì kể truyện mở chương trước. */
  const vaoChienDich = useCallback(async () => {
    const b = boot ?? await napBoot()
    const c = b?.chuong.find(x => x.mo) ?? b?.chuong[0]
    if (!c) return
    setChuongId(c.id)
    setManId(id => id ?? b?.man_tiep ?? c.man[0]?.id ?? null)
    const r = await pyGame.truyen(c.id, 'mo')
    if (r.ok && r.value && !r.value.da_xem) await xemTruyen(c.id, 'mo', 'chon_man')
    else setManHinh('chon_man')
  }, [boot, napBoot, xemTruyen])

  const chonMan = useCallback(async (id: string) => {
    setManId(id)
    await napPhieu(id)
  }, [napPhieu])

  const moPhieu = useCallback(async (id: string) => {
    setManId(id)
    setLoi('')
    await napPhieu(id)
    setManHinh('phieu')
  }, [napPhieu])

  /** Vào xưởng: nạp máy gợi ý / bắt đầu trắng / giữ cỗ máy đang vẽ. */
  const vaoXuong = useCallback(async (cach: 'goi_y' | 'trang' | 'giu') => {
    const m = phieu
    if (cach === 'goi_y' && m?.may_goi_y) {
      const r = await pyGame.may(m.may_goi_y)
      if (r.ok && r.value) cnRef.current.napSoDo(r.value, `◆ ${m.id} — nạp máy gợi ý «${r.value.name}»`)
    } else if (cach === 'trang') {
      const r = await py.new_process()
      if (r.ok && r.value) cnRef.current.napSoDo(r.value, `◆ ${m?.id ?? ''} — bắt đầu từ sơ đồ trắng`)
    }
    setPhat(null)
    setManHinh('xuong')
    if (m) void napPhieu(m.id)
  }, [phieu, napPhieu])

  const veBanDo = useCallback(async () => {
    setPhat(null)
    setLoi('')
    cnRef.current.soi(null)
    await napBoot()
    setManHinh('chon_man')
  }, [napBoot])

  /* ------------------------------ chạy ------------------------------ */
  const chay = useCallback(async (loai: LoaiChay) => {
    setLoi('')
    setPhat(null)
    cnRef.current.soi(null)
    const r = await pyGame.chay(cnRef.current.laySoDo(), loai, manId, null)
    if (!r.ok) {
      const ds = ((r as { loi?: Problem[] }).loi ?? []).map(p => '✖ ' + p.message)
      setLoi([r.error ?? 'không chạy được', ...ds].join('\n'))
      return
    }
    setTt({ dang_chay: true, loai, chu: 'Đóng gói cỗ máy', ti_le_chung: 0, xong: null, loi: null })
    if (loai === 'nop') { setNop(null); setManHinh('nop') }
  }, [manId])

  /** Mở màn hình ĐẤU MÀN ẨN — chưa chạy gì: người chơi thấy đối thủ, bấm «Bắt đầu» mới
   *  nộp. Mỗi lần nộp được đếm (D-06), nên không để một cú bấm nhầm trên thanh xưởng
   *  thành một lần nộp. */
  const moNop = useCallback(() => {
    setLoi('')
    setNop(null)
    setPhat(null)
    cnRef.current.soi(null)
    setManHinh('nop')
  }, [])

  /* Hỏi tiến độ khi đang chạy; xong thì sang màn hình kết quả / mở màn ẩn. */
  useEffect(() => {
    if (!tt?.dang_chay) return
    const id = window.setInterval(async () => {
      if (dangHoi.current) return
      dangHoi.current = true
      try {
        const r = await pyGame.trangThai()
        if (!r.ok || !r.value) return
        setTt(r.value)
        if (r.value.dang_chay) return
        if (r.value.loi) { setLoi(r.value.loi); return }
        const x = r.value.xong
        if (!x) return
        if (x.an) {
          setNop(x)
          await napBoot()
          if (manId) await napPhieu(manId)
        } else {
          setKq(x)
          if (manId) await napPhieu(manId)
          setManHinh('ket_qua')
          cnRef.current.ghi(`◆ ${x.loai === 'nhanh' ? '▶ nhanh' : '▶ đầy đủ'} xong — `
                            + `cỗ máy ${x.cham?.lai_pt ?? x.thong_ke.lai_pt} % · boss `
                            + `${x.cham?.mua_giu_pt ?? '—'} %`, 'ok')
        }
      } finally { dangHoi.current = false }
    }, NHIP_HOI)
    return () => window.clearInterval(id)
  }, [tt?.dang_chay, manId, napBoot, napPhieu])

  /** Sau màn hình đấu màn ẩn: màn vừa xong lần đầu → màn hình hoàn thành; không thì về xưởng. */
  const sauNop = useCallback(async () => {
    const b = await napBoot()
    const x = nop
    if (!b || !x || !manId) { setManHinh('xuong'); return }
    const ds = b.chuong.flatMap(c => c.man)
    const k = ds.findIndex(m => m.id === manId)
    const m = ds[k]
    const manTiep = ds[k + 1] && ds[k + 1].chuong === m.chuong ? ds[k + 1] : null
    const c = b.chuong.find(cc => cc.id === m.chuong)
    const xongChuong = !!c && c.man.every(mm => mm.tien_do.sao >= 1)
    if ((x.sao ?? 0) >= 1) {
      setHoanThanh({ man: m, sao: x.sao ?? 0, lanNop: x.lan_nop ?? 0, manTiep, xongChuong })
      setManHinh('hoan_thanh')
    } else {
      setManHinh('xuong')
    }
  }, [napBoot, nop, manId])

  const sauHoanThanh = useCallback(async (diTiep: boolean) => {
    const h = hoanThanh
    setHoanThanh(null)
    if (h?.xongChuong) {
      const r = await pyGame.truyen(h.man.chuong, 'dong')
      if (r.ok && r.value && !r.value.da_xem) {
        await xemTruyen(h.man.chuong, 'dong', 'chon_man')
        return
      }
    }
    if (diTiep && h?.manTiep) await moPhieu(h.manTiep.id)
    else await veBanDo()
  }, [hoanThanh, xemTruyen, moPhieu, veBanDo])

  /* ------------------------------ xem máy nghĩ (phát lại) ------------------------------ */
  const toiLuot = useCallback(async (p: PhatLai, k: number) => {
    const d = p.ds[k]
    if (!d) return p
    const r = await pyGame.luot(d.i)
    if (r.ok && r.value) cnRef.current.soi(r.value)
    return { ...p, k, chu: d.chu, luot: r.ok ? r.value ?? null : null }
  }, [])

  const xemMayNghi = useCallback(async (chiViec = true) => {
    const r = await pyGame.nhatKy(0, LO_PHAT, chiViec)
    if (!r.ok || !r.value || !r.value.dong.length) {
      setLoi(r.error ?? 'Lượt này chưa có việc gì để xem — thử bật «mọi lượt».')
      return
    }
    setManHinh('xuong')
    const p0: PhatLai = { ds: r.value.dong, tong: r.value.tong, k: 0, phat: false, toc: 1,
                          chiViec, chu: '', luot: null }
    setPhat(await toiLuot(p0, 0))
  }, [toiLuot])

  const buocPhat = useCallback(async (d: number) => {
    if (!phat) return
    const k = Math.max(0, Math.min(phat.ds.length - 1, phat.k + d))
    setPhat(await toiLuot(phat, k))
  }, [phat, toiLuot])

  const nhayPhat = useCallback(async (k: number) => {
    if (!phat) return
    setPhat(await toiLuot(phat, Math.max(0, Math.min(phat.ds.length - 1, k))))
  }, [phat, toiLuot])

  const datPhat = useCallback((v: Partial<PhatLai>) => {
    setPhat(p => (p ? { ...p, ...v } : p))
  }, [])

  const tatPhat = useCallback(() => {
    setPhat(null)
    cnRef.current.soi(null)
  }, [])

  /* Phát: mỗi nhịp sang lượt kế; tốc độ ×1 = 1,2 lượt/giây. */
  useEffect(() => {
    if (!phat?.phat) return
    const id = window.setTimeout(async () => {
      if (phat.k >= phat.ds.length - 1) { setPhat(p => (p ? { ...p, phat: false } : p)); return }
      setPhat(await toiLuot(phat, phat.k + 1))
    }, 830 / phat.toc)
    return () => window.clearTimeout(id)
  }, [phat, toiLuot])

  return {
    bat, manHinh, setManHinh, boot, chuongId, setChuongId, manId, man, phieu, truyen, tt, loi,
    setLoi, kq, nop, phat, hoanThanh,
    moGame, thoatGame, vaoChienDich, chonMan, moPhieu, vaoXuong, veBanDo, napPhieu, napBoot,
    truyenTiep, boQuaTruyen, xemTruyen, chay, moNop, sauNop, sauHoanThanh,
    xemMayNghi, buocPhat, nhayPhat, datPhat, tatPhat,
    dangChay: !!tt?.dang_chay,
  }
}

export type Game = ReturnType<typeof useGame>
