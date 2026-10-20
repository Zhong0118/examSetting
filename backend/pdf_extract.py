"""Resource-bounded PDF extraction worker. Invoked by documents in a subprocess."""
import json
import sys

MAX_PAGES = 200
MAX_TEXT_CHARS = 2_000_000


def extract_pdf(path):
    from pypdf import PdfReader

    reader = PdfReader(path, strict=True)
    if reader.is_encrypted:
        raise ValueError('不支持加密 PDF，请先提供未加密版本')
    count = len(reader.pages)
    if not 1 <= count <= MAX_PAGES:
        raise ValueError('PDF 必须包含 1 至 200 个物理页')
    pages, warnings = [], []
    total = 0
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        total += len(text)
        if total > MAX_TEXT_CHARS:
            raise ValueError('PDF 全文超过 200 万字符，请拆分文件')
        if not text.strip():
            text = ''
            warnings.append(f'物理第 {number} 页未提取到文字，本版本不提供 OCR')
        pages.append(dict(page=number, text=text, charCount=len(text)))
    if not any(p['text'] for p in pages):
        raise ValueError('PDF 没有可提取文字，本版本不提供扫描件 OCR')
    return dict(pages=pages, warnings=warnings)


def main():
    import os
    import resource
    import signal

    # Limits apply only to this disposable worker, never to Flask.
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    memory_limit = 512 * 1024 * 1024
    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
    except (ValueError, OSError):
        # macOS rejects RLIMIT_AS changes. Check peak RSS periodically instead;
        # the parent's wall-clock timeout still kills an unresponsive worker.
        def check_memory(signum, frame):
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            if sys.platform != 'darwin':
                rss *= 1024
            if rss > memory_limit:
                os._exit(1)
        signal.signal(signal.SIGALRM, check_memory)
        signal.setitimer(signal.ITIMER_REAL, 0.05, 0.05)
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024 * 1024, 16 * 1024 * 1024))
    try:
        result = extract_pdf(sys.argv[1])
    except ValueError as error:
        result = {'error': str(error)}
    except Exception:
        result = {'error': 'PDF 损坏、格式无效或解析资源超限，请尝试更小的有效 PDF'}
    finally:
        # Do not leave SIGALRM armed while Python restores handlers on exit.
        signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
