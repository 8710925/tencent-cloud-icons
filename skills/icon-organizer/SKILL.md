---
name: icon-organizer
description: |
  Organize cloud product icon SVG files from PPTX into categorized folders. This skill extracts product names and categories from PowerPoint files containing cloud service icons, then moves SVG files into the appropriate category directories following a standardized naming convention (like Alibaba Cloud's icon library structure). Use this skill when organizing cloud vendor icon libraries (Tencent Cloud, Alibaba Cloud, etc.) from PPTX source files into draw.io-compatible folder structures.
---

# Icon Organizer Skill

Organize cloud product icon SVG files from PPTX into categorized folders based on product classifications.

## Features

- **PPTX Category Extraction**: Automatically extracts product categories from PowerPoint files
- **Smart Matching**: Uses fuzzy matching and word overlap algorithms to match filenames to products
- **NBSP Handling**: Properly handles non-breaking space characters (NBSP, `\xa0`) in filenames
- **Filename Normalization**: Renames files to use regular spaces during organization
- **Built-in Categories**: Includes pre-configured categories for Tencent Cloud (Chinese and English)
- **Dry Run Mode**: Preview changes without actually moving files
- **Detailed Reporting**: Shows matched, unmatched, and remaining files

## When to Use

- Organizing cloud vendor icon libraries (Tencent Cloud, Alibaba Cloud, AWS, etc.)
- Extracting product categorization from PPTX files
- Moving SVG icon files into categorized directory structures
- Creating draw.io-compatible icon library folder structures

## Quick Start

### Basic Usage with Built-in Categories

```bash
# Organize Chinese icons
python3 scripts/organize_icons.py --icons-dir /path/to/icons/zh --language zh

# Organize English icons
python3 scripts/organize_icons.py --icons-dir /path/to/icons/en --language en
```

### Preview Mode (Dry Run)

```bash
python3 scripts/organize_icons.py --icons-dir /path/to/icons --language zh --dry-run
```

### With Custom PPTX File

```bash
python3 scripts/organize_icons.py \
  --icons-dir /path/to/icons \
  --pptx /path/to/product_icons.pptx \
  --language zh
```

### With Custom Categories JSON

```bash
python3 scripts/organize_icons.py \
  --icons-dir /path/to/icons \
  --categories-file /path/to/categories.json
```

## Detailed Workflow

### Step 1: Prepare Your Icons

Ensure your SVG icon files are in a single directory. The script will:
1. Scan for all `.svg` files in the directory
2. Create category subdirectories
3. Move files to appropriate categories

### Step 2: Choose Category Source

You have three options:

#### Option A: Use Built-in Categories (Recommended for Tencent Cloud)

The script includes comprehensive category mappings for Tencent Cloud products in both Chinese and English. Simply specify the language:

```bash
--language zh  # Chinese categories (01 计算, 02 容器与中间件, etc.)
--language en  # English categories (01 Compute, 02 Container And Middleware, etc.)
```

#### Option B: Extract from PPTX

If you have a PPTX file containing product categories (like the official Tencent Cloud icon PPTX):

```bash
--pptx /path/to/tencent_cloud_product_icons_zh.pptx
```

The script will:
1. Extract the PPTX (which is a ZIP archive)
2. Parse XML content from slides
3. Identify category headers and product names
4. Build a category mapping automatically

#### Option C: Custom JSON File

Create a JSON file with your own category mapping:

```json
{
  "01 Category Name": ["Product A", "Product B", "Product C"],
  "02 Another Category": ["Product D", "Product E"]
}
```

### Step 3: Run the Organization

```bash
cd /path/to/icon-organizer
python3 scripts/organize_icons.py \
  --icons-dir /path/to/icons \
  --language zh
```

The script performs two passes:
1. **First Pass**: Match products to SVG files using smart matching
2. **Second Pass**: Handle remaining files with more relaxed matching

### Step 4: Review Results

The script outputs:
- Files moved to each category
- Unmatched products (no SVG file found)
- Remaining files (could not be automatically categorized)

Example output:
```
Found 455 SVG files to organize
Categories: 17

============================================================
Category: 01 计算
============================================================
  ✓ 云服务器.svg
  ✓ GPU 云服务器.svg
  ✓ 弹性伸缩.svg
  Matched: 31/35 products

...

============================================================
SUMMARY
============================================================
Total SVG files found: 455
Files moved: 450
Files remaining: 5

Remaining SVG files (5):
  - Special Product Name.svg
  - Another Unmatched.svg
```

## Handling Special Cases

### Non-Breaking Spaces (NBSP)

Some filenames may contain NBSP (`\xa0`) instead of regular spaces. The script:
1. Detects NBSP in filenames
2. Matches them correctly to products
3. Renames files to use regular spaces when moving

### Version Suffixes

Files with version suffixes like `-1`, `-2` are handled:
- `云服务器.svg` matches "云服务器"
- `云服务器-1.svg` also matches "云服务器"

### Fuzzy Matching

The script uses multiple strategies:
1. **Exact match**: Normalized names match exactly
2. **Base name match**: Ignoring version suffixes
3. **Similarity score**: Using sequence matcher (60%+ threshold)
4. **Word overlap**: Common words between names

## Directory Structure

The final structure follows this pattern:

```
icons/
├── 01 计算/
│   ├── 云服务器.svg
│   ├── GPU 云服务器.svg
│   └── ...
├── 02 容器与中间件/
│   ├── 容器服务.svg
│   └── ...
├── 03 存储/
│   └── ...
...
└── 17 服务与营销/
    └── ...
```

## Category Reference

### Chinese Categories (zh)

| # | Category | Description |
|---|----------|-------------|
| 01 | 计算 | Compute services |
| 02 | 容器与中间件 | Container and Middleware |
| 03 | 存储 | Storage |
| 04 | 数据库 | Database |
| 05 | 网络 | Network |
| 06 | CDN与边缘 | CDN and Edge |
| 07 | 视频服务 | Video Services |
| 08 | 安全 | Security |
| 09 | 大数据 | Big Data |
| 10 | 人工智能与机器学习 | AI and ML |
| 11 | 开发与运维 | Development and Operations |
| 12 | 云通信与企业服务 | Cloud Communication and Enterprise |
| 13 | 办公协同 | Office Collaboration |
| 14 | 微信生态 | WeChat Ecosystem |
| 15 | 物联网 | Internet of Things |
| 16 | 行业应用 | Industry Applications |
| 17 | 服务与营销 | Service and Marketing |

### English Categories (en)

| # | Category |
|---|----------|
| 01 | Compute |
| 02 | Container And Middleware |
| 03 | Storage |
| 04 | Tencentdb |
| 05 | Network |
| 06 | Cdn And Cloud Communication |
| 07 | Video |
| 08 | Security |
| 09 | Bigdata |
| 10 | Artificial Intelligence And Machine Learning |
| 11 | Development And Operation |
| 12 | Enterprise And Communication |
| 13 | Office Collaboration |
| 14 | Wechat Ecosystem |
| 15 | Internet Of Things |
| 16 | Industry |
| 17 | Service Marketing |

## Files

- `scripts/organize_icons.py` - Main organization script with all features
- `references/category_naming.md` - Category naming conventions reference

## Troubleshooting

### Files Not Being Matched

1. Check if the product name in categories matches the filename
2. Use `--verbose` flag for detailed matching information
3. Try running with `--dry-run` first to see matches

### PPTX Extraction Not Working

1. Ensure the PPTX file is not corrupted
2. Check if the PPTX contains text in expected format
3. Fall back to using built-in categories or custom JSON

### Permission Errors

1. Ensure you have write permission to the icons directory
2. Check if files are not locked by another process
