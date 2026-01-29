# Icon Organizer

自动整理云产品图标文件到分类目录的工具。

## 功能特性

- ✅ **PPTX 解析**: 从 PowerPoint 文件自动提取产品分类信息
- ✅ **智能匹配**: 使用模糊匹配和词重叠算法匹配文件名到产品
- ✅ **NBSP 处理**: 正确处理文件名中的不间断空格字符
- ✅ **内置分类**: 预配置腾讯云产品分类（中英文）
- ✅ **预览模式**: 支持 `--dry-run` 预览变更
- ✅ **多格式支持**: 支持 SVG、PNG 等图标格式

## 快速使用

```bash
# 整理中文 SVG 图标
python3 scripts/organize_icons.py --icons-dir /path/to/icons/zh --language zh

# 整理英文 PNG 图标
python3 scripts/organize_icons.py --icons-dir /path/to/icons/en --language en --extension png

# 预览模式
python3 scripts/organize_icons.py --icons-dir /path/to/icons --language zh --dry-run
```

## 目录结构

```
icon-organizer/
├── README.md                    # 本文件
├── SKILL.md                     # CodeBuddy Skill 配置
├── scripts/
│   └── organize_icons.py        # 主脚本（942行）
└── references/
    └── category_naming.md       # 分类命名规范
```

## 支持的分类

整理完成后，图标会按照 17 个分类进行组织：

| # | 中文分类 | 英文分类 |
|---|---------|---------|
| 01 | 计算 | Compute |
| 02 | 容器与中间件 | Container And Middleware |
| 03 | 存储 | Storage |
| 04 | 数据库 | Tencentdb |
| 05 | 网络 | Network |
| 06 | CDN与边缘 | Cdn And Cloud Communication |
| 07 | 视频服务 | Video |
| 08 | 安全 | Security |
| 09 | 大数据 | Bigdata |
| 10 | 人工智能与机器学习 | Artificial Intelligence And Machine Learning |
| 11 | 开发与运维 | Development And Operation |
| 12 | 云通信与企业服务 | Enterprise And Communication |
| 13 | 办公协同 | Office Collaboration |
| 14 | 微信生态 | Wechat Ecosystem |
| 15 | 物联网 | Internet Of Things |
| 16 | 行业应用 | Industry |
| 17 | 服务与营销 | Service Marketing |

## 添加新产品

如果有图标未能自动匹配，编辑 `scripts/organize_icons.py` 中的字典：
- `TENCENT_CLOUD_CATEGORIES_ZH` - 中文产品名称
- `TENCENT_CLOUD_CATEGORIES_EN` - 英文产品名称

## 详细文档

更多信息请参阅 [SKILL.md](./SKILL.md)
