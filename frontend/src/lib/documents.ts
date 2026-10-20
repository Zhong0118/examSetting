/// <reference lib="es2022.intl" />
import type { DocumentPage } from './api'
export function normalizeQuote(value: string) { return value.normalize('NFKC').replace(/\s+/gu,' ').trim() }
export function selectionError(pages: DocumentPage[], start: number, end: number) {
  if(!Number.isInteger(start)||!Number.isInteger(end)||start<1||end<start||end>pages.length)return '请输入有效的 PDF 物理页范围'
  if(end-start+1>20)return '每次最多选择 20 页，请缩小页范围'
  const count=pages.filter(p=>p.page>=start&&p.page<=end).map(p=>p.text).join('\n\n').length
  if(count>30000)return '所选页文字超过 30000 字，请缩小范围；不会自动截断'
  if(count<20)return '所选页文字不足 20 字，请选择有文字的页面；不支持 OCR'
  return ''
}
// Preserve original text while matching the same NFKC/whitespace convention as citations.
export function highlightQuote(text: string, quote: string) {
  if(!normalizeQuote(quote))return [{text,highlight:false}]
  const decomposed:string[]=[],offsets:{start:number;end:number}[]=[]
  let offset=0
  // Decompose first so compatibility Jamo can form a single canonical cluster.
  // Each UTF-16 unit retains its original range; no prefix normalization scans.
  for(const char of text){
    const part=char.normalize('NFKD'),range={start:offset,end:offset+char.length}
    decomposed.push(part)
    for(let i=0;i<part.length;i++)offsets.push(range)
    offset+=char.length
  }
  const original: {start:number;end:number}[]=[],normalized: string[]=[]
  for(const {segment,index} of new Intl.Segmenter(undefined,{granularity:'grapheme'}).segment(decomposed.join(''))){
    const start=offsets[index].start,end=offsets[index+segment.length-1].end
    for(const value of segment.normalize('NFC')){
      if(/\s/u.test(value)){
        if(normalized.at(-1)===' '){original[original.length-1].end=end;continue}
        normalized.push(' ')
      }else normalized.push(value)
      original.push({start,end})
    }
  }
  const needle=normalizeQuote(quote),joined=normalized.join(''),at=joined.indexOf(needle)
  if(at<0)return [{text,highlight:false}]
  // Offsets are UTF-16 for indexOf, including non-BMP characters.
  const map=normalized.flatMap((value,i)=>Array.from({length:value.length},()=>original[i]))
  const start=map[at].start,end=map[at+needle.length-1].end
  return [{text:text.slice(0,start),highlight:false},{text:text.slice(start,end),highlight:true},{text:text.slice(end),highlight:false}]
}
export function percent(value: number | null | undefined) { return typeof value==='number'&&Number.isFinite(value)?`${(value*100).toFixed(1)}%`:'—' }
export function downloadJSON(value: unknown, filename: string) {
  const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}))
  const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)
}

export function qualityLabel(code: string) {
  const labels: Record<string,string>={structure:'题目结构',answer:'参考答案',explanation:'答案解析',citation:'引用完整性',citation_snapshot:'引用快照',citation_authority:'原教材核验',duplicate:'题目重复'}
  return labels[code]||'其他检查项'
}
