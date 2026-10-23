// Bảng dịch của giao diện web ra JSON { câu: bản tiếng Anh } — cho bộ công cụ song ngữ phía
// Python (`tools/dich_python.py`): câu có ở cả hai bảng thì hai bản tiếng Anh phải giống hệt,
// và câu Python còn thiếu mà web đã có thì lấy sẵn bản của web. Chỉ ĐỌC.
import { docBang } from './soat.mjs'

const ra = {}
for (const [k, v] of docBang().bang) ra[k] = v.en
process.stdout.write(JSON.stringify(ra))
