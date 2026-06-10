import pdfplumber
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf = pdfplumber.open('열역학테이블.pdf')
print(f'총 페이지: {len(pdf.pages)}')

for i, page in enumerate(pdf.pages):
    text = page.extract_text()
    tables = page.extract_tables()
    print(f'\n=== 페이지 {i+1} ===')
    if text:
        print('텍스트 (첫 500자):')
        print(text[:500])
    else:
        print('(텍스트 없음 - 스캔 이미지일 가능성)')
    print(f'표 개수: {len(tables)}')
    for j, tbl in enumerate(tables[:2]):
        print(f'  표 {j+1} (첫 5행):')
        for row in tbl[:5]:
            print('   ', row)
