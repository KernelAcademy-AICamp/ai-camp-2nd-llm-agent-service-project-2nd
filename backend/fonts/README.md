# Korean Fonts for Legal Document Export

This directory contains Korean fonts required for PDF generation using WeasyPrint.

## Required Fonts

1. **Noto Serif CJK KR** (Primary - Open Source)
   - Download from: https://github.com/googlefonts/noto-cjk/releases
   - File: `NotoSerifCJKkr-Regular.otf`
   - License: SIL Open Font License (free for commercial use)

2. **Batang** (Traditional legal document font)
   - Included with Korean Windows systems
   - Alternative: Use Noto Serif CJK KR as fallback

## Installation

### Option 1: Use Noto Serif CJK KR (Recommended)

```bash
# Download Noto Serif CJK KR
curl -L -o NotoSerifCJK.zip https://github.com/googlefonts/noto-cjk/releases/download/Serif2.003/05_NotoSerifCJKkr.zip
unzip NotoSerifCJK.zip -d .
mv NotoSerifCJKkr-Regular.otf .
rm -rf NotoSerifCJK.zip OFL.txt README*
```

### Option 2: Docker (for deployment)

Add to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*
```

## Font Files Expected

- `NotoSerifCJKkr-Regular.otf` - Primary Korean serif font
- `Batang.ttf` (optional) - Traditional Korean legal font

## Verification

After installing fonts, verify with:
```bash
python -c "from weasyprint import HTML; print('WeasyPrint OK')"
```

## Notes

- Korean legal documents traditionally use Batang (serif) font at 12pt
- Noto Serif CJK KR is an excellent open-source alternative
- PDF generation requires system-level font installation for WeasyPrint
