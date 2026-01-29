#!/usr/bin/env python3
"""
Organize cloud product icon SVG files into categorized folders.

This script is designed to work with Tencent Cloud icon libraries, extracting
product categorization from PPTX files and organizing SVG icons accordingly.

Usage:
    # Basic usage with built-in categories
    python3 organize_icons.py --icons-dir <path> --language <zh|en>

    # With PPTX file to extract categories
    python3 organize_icons.py --icons-dir <path> --pptx <path_to_pptx> --language <zh|en>

    # Dry run mode (preview changes without moving files)
    python3 organize_icons.py --icons-dir <path> --language <zh|en> --dry-run

Features:
    - Handles NBSP (non-breaking space) characters in filenames
    - Fuzzy matching for product names
    - Extracts categories from PPTX files
    - Normalizes filenames (replaces NBSP with regular space)
    - Reports unmatched files for manual review
"""

import os
import re
import shutil
import argparse
import json
import zipfile
import tempfile
from pathlib import Path
from difflib import SequenceMatcher
from xml.etree import ElementTree as ET


# Non-breaking space character
NBSP = '\xa0'


# =============================================================================
# DEFAULT CATEGORY MAPPINGS FOR TENCENT CLOUD
# =============================================================================

TENCENT_CLOUD_CATEGORIES_ZH = {
    "01 计算": [
        "云服务器", "轻量应用服务器", "弹性伸缩", "裸金属云服务器", "黑石物理服务器",
        "云服务器专用宿主机", "专用宿主机", "批量计算", "GPU云服务器", "GPU 云服务器",
        "高性能计算", "高性能计算集群", "高性能计算集群-1", "高性能计算平台", "高性能应用服务",
        "边缘可用区", "专属可用区", "本地专用集群", "容器镜像服务", "容器镜像服务-1",
        "TencentOS Server", "异构计算加速套件", "计算加速套件 TACO Kit",
        "Tencent Kona", "腾讯 Kona", "云命令行", "云函数", "云函数-1",
        "Serverless应用中心", "Serverless 应用中心", "Serverless 应用中心-1",
        "Serverless HTTP", "Serverless HTTP 服务", "Serverless HTTP 服务-1",
        "Serverless SSR", "Serverless  SSR", "Serverless  SSR-1", "Serverless 容器服务",
        "FPGA云服务器", "FPGA 云服务器", "云服务器-1", "腾讯云遨驰终端", "腾讯云遨驰终端-1",
        "云托付物理服务器", "高性能计算集群 HCC",
    ],
    "02 容器与中间件": [
        "容器服务", "弹性容器服务", "边缘容器服务", "腾讯云边缘容器服务",
        "消息队列CKafka", "消息队列 CKafka 版", "消息队列RocketMQ", "消息队列 RocketMQ 版",
        "消息队列RabbitMQ", "消息队列 RabbitMQ 版", "消息队列Pulsar", "消息队列 Pulsar 版",
        "消息队列CMQ", "消息队列 CMQ 版", "API网关", "API 网关", "服务网格",
        "云原生API网关", "云原生 API 网关", "微服务引擎", "注册配置中心",
        "北极星网格", "Mesh 微服务平台", "弹性微服务", "微服务平台TSF", "微服务平台 TSF",
        "Serverless函数", "云监控", "云监控-1", "云监控-2", "腾讯云可观测平台",
        "应用性能观测", "应用性能监控", "前端性能监控", "云拨测", "云拨测-1",
        "自动化测试", "Prometheus监控", "Prometheus 监控服务", "Prometheus 监控服务-1",
        "Grafana可视化服务", "Grafana 服务", "Grafana 服务-1", "事件总线", "事件总线-1",
        "混沌演练平台", "混沌演练平台-1", "日志服务", "日志服务-1", "日志服务-2",
    ],
    "03 存储": [
        "对象存储", "轻量对象存储", "文件存储", "云硬盘", "归档存储",
        "云HDFS", "云 HDFS", "数据湖加速器", "数据加速器 GooseFS", "数据万象",
        "图片处理", "媒体处理", "多媒体处理", "文档服务", "图片审核", "文本审核",
        "音频审核", "视频审核", "文档审核", "内容识别", "智能媒资托管",
        "迁移服务平台", "云数据迁移", "存储网关", "TStor存储", "TStor B2000",
        "并行文件系统", "智能视图计算", "存储一体机", "备份一体机", "并行文件一体机",
    ],
    "04 数据库": [
        "云原生数据库TDSQL-C", "云原生数据库 TDSQL-C", "CynosDB", "TDSQL-C PostgreSQL",
        "TDSQL-C MySQL 版", "云数据库MySQL", "云数据库 MySQL", "云数据库MariaDB",
        "云数据库 MariaDB", "云数据库SQL Server", "云数据库 SQL Server",
        "云数据库PostgreSQL", "云数据库 PostgreSQL", "轻量数据库",
        "分布式数据库TDSQL", "分布式数据库 TDSQL", "TDSQL MySQL", "TDSQL PostgreSQL 版",
        "云数据库TBase", "HTAP数据库TDSQL-H", "HTAP 数据库 TDSQL-H",
        "TDSQL-H TxLightning", "TDSQL-H LibraDB", "云数据库Redis", "云数据库 Redis",
        "云数据库MongoDB", "云数据库 MongoDB", "云数据库Memcached", "云数据库 Memcached",
        "时序数据库CTSDB", "时序数据库 CTSDB", "游戏数据库TcaplusDB", "游戏数据库 TcaplusDB",
        "云数据库KeeWiDB", "云数据库 KeeWiDB", "向量数据库", "数据库一体机TData",
        "数据库一体机 TData", "数据库专属集群", "云数据库独享集群", "数据传输服务",
        "数据库专家服务", "数据库智能管家", "数据库备份服务", "数据库管理",
        "数据库分布式云中心",
    ],
    "05 网络": [
        "负载均衡", "私有网络", "弹性网卡", "NAT网关", "NAT 网关", "流日志",
        "Anycast公网加速", "Anycast 公网加速", "共享带宽包", "共享流量包",
        "弹性公网IPv6", "弹性公网 IPv6", "弹性公网IP", "弹性公网 IP",
        "私有连接", "专线接入", "云联网", "VPN连接", "VPN 连接",
        "5G入云服务", "对等连接", "SD-WAN接入服务", "SD-WAN 接入服务",
        "DNS解析", "私有域解析 Private DNS", "HTTPDNS", "智能调度", "全局流量管理",
        "云解析 DNS", "云解析DNS", "负载主", "负载大师",
    ],
    "06 CDN与边缘": [
        "边缘安全加速平台", "内容分发网络", "全站加速网络", "DDoS防护",
        "DDoS 防护", "DDoS 防护-1", "全球加速", "全球应用加速", "多网聚合加速",
        "边缘计算机器",
    ],
    "07 视频服务": [
        "实时音视频", "即时通信IM", "即时通信 IM", "即时通信 IM-1",
        "云呼叫中心", "云联络中心", "云联络中心-1", "语音消息",
        "低代码互动课堂", "实时互动TRTC", "实时互动-教育版", "实时互动-工业能源版",
        "实时互动-物联版", "物联网智能视频", "游戏多媒体引擎", "云直播",
        "标准直播", "慢直播", "快直播", "直播SDK", "直播 SDK", "云点播",
        "媒体处理", "极速高清", "智能识别", "智能审核", "智能编辑", "智能创作",
        "云游戏", "云桌面", "应用云渲染", "X-P2P", "音视频终端引擎",
        "音视频终端 SDK(腾讯云视立方)", "视频通话SDK", "音视频通话 SDK",
        "短视频SDK", "短视频 SDK", "美颜特效SDK", "腾讯特效 SDK",
        "播放器SDK", "播放器 SDK", "虚拟形象SDK", "虚拟形象 SDK",
        "会议SDK", "多人音视频房间 SDK", "媒体传输", "企业版媒体处理", "媒体处理企业版",
        "腾讯云智绘", "VR 实景漫游", "TRTC云助手", "短视频创作", "云导播台",
    ],
    "08 安全": [
        "云防火墙", "安全运营中心", "云安全中心", "Web应用防火墙", "Web 应用防火墙",
        "API安全", "API 安全治理", "漏洞扫描服务", "网络入侵防护系统", "网络流量分析系统",
        "威胁情报云查", "威胁情报云查与本地引擎", "威胁情报", "威胁情报中心",
        "高级威胁检测系统", "攻击面管理", "威胁情报攻击面管理", "安全数据湖", "安全湖",
        "主机安全", "容器安全服务", "微隔离", "微隔离服务", "数据安全治理中心",
        "云访问安全代理", "数据安全平台", "数据安全审计",
        "密钥管理系统", "凭据管理系统", "云加密机", "机密计算平台", "可信计算服务",
        "数据脱敏", "堡垒机", "数据保险箱", "SSL证书", "SSL 证书", "SSL 证书-1",
        "SSL证书专属版", "证书监控 SSLPod", "云证通", "邮件证书",
        "腾讯云 CA", "腾讯云 CA-1", "账号连接器",
        "代码签名证书", "数字身份管控", "数字身份管控平台", "数字身份管控平台（员工版）",
        "数字身份管控平台（公众版）", "访问管理", "身份治理",
        "验证码", "账号安全", "账号安全服务", "业务风险情报", "流量反欺诈", "反欺诈",
        "安全托管服务", "移动安全", "移动应用安全", "渗透测试", "渗透测试服务",
        "安全专家服务", "攻防演练", "安全攻防对抗服务", "重保服务", "重要时期安全保障服务",
        "文本内容安全", "图片内容安全", "音频内容安全", "视频内容安全",
        "营销号码安全", "联邦学习", "腾讯安心用户运营平台", "应用合规平台",
        "全栈式风控引擎", "设备安全", "游戏安全", "服务性能测试", "小程序安全",
        "测试服务", "标准兼容测试", "专家兼容测试", "远程调试", "手游安全测试",
        "品牌经营管家", "应急响应服务", "安全平台服务", "暴露面管理服务",
        "漏洞治理服务", "安全验证服务", "云安全风险巡检服务", "应用安全开发",
        "二进制软件成分分析", "iOA 零信任安全管理系统", "人脸核身",
    ],
    "09 大数据": [
        "弹性MapReduce", "弹性 MapReduce", "弹性 MapReduce-1",
        "WeData数据开发平台", "数据集成", "数据湖计算",
        "流计算Oceanus", "流计算 Oceanus", "流计算 Oceanus-1",
        "云数据仓库ClickHouse", "云数据仓库 ClickHouse", "云数据仓库 PostgreSQL",
        "数据湖构建DLF", "数据湖构建 DLF", "Elasticsearch服务", "Elasticsearch Service",
        "图计算", "流式数据仓库", "数据仓库", "商业智能分析BI", "商业智能分析 BI",
        "大数据可视交互系统", "风控平台", "数据分类分级", "数据资产管理", "隐私计算",
        "腾讯云数据仓库 TCHouse-D", "商场客留大数据", "大数据处理套件 TBDS",
        "大数据处理套件TBDS", "数据开发治理平台 WeData", "数据开发治理平台WeData",
        "数据湖分析", "腾讯云 BI", "腾讯云BI",
    ],
    "10 人工智能与机器学习": [
        "TI平台", "腾讯云 TI 平台", "腾讯混元", "语音识别", "语音合成", "语音合成工坊",
        "自然语言处理", "NLP 服务", "机器翻译", "同声传译", "人脸识别",
        "人脸特效", "人脸融合", "人脸融合-1", "人体分析", "图像识别",
        "图像处理", "智能鉴黄", "文字识别", "智能结构化", "内容审核",
        "智能对话分析", "音乐标签", "情感分析", "知识图谱", "腾讯知识图谱",
        "智能导诊", "智能预问诊", "对话机器人", "智能客服机器人",
        "智能外呼", "智能语音质检", "智能会话质检", "数智人",
        "智能语音服务", "智能硬件AI语音助手", "智能媒资检测",
        "图像标签", "图像质量检测", "口语评测", "口语评测(中文版)", "口语评测(英文版)",
        "语音评测", "作文批改-英文", "作业批改-数学",
        "英文作文批改", "数学作业批改", "腾讯同传", "腾讯觅影开放实验平台",
        "图像理解", "视频理解", "声音工坊", "腾讯云小微", "图像创作",
        "智能硬件 AI 语音助手",
    ],
    "11 开发与运维": [
        "CODING DevOps", "CODING CI", "CODING 持续集成", "CODING CD", "CODING 持续部署",
        "CODING制品库", "CODING 制品库", "CODING测试管理", "CODING 测试管理",
        "CODING项目管理", "CODING 项目管理", "CODING Insight", "CODING 代码托管",
        "Cloud Studio", "自动化助手", "Terraform", "腾讯云 IaC", "云顾问",
        "配置审计", "云审计", "资源编排", "资源编排 TIC", "企业组织", "健康看板",
        "消息中心", "事件中心", "标签", "成本管理", "代码分析", "WeTest",
        "远程调试", "云测试服务", "专家兼容测试", "性能测试服务",
        "TAPD 敏捷项目管理", "云 API", "腾讯云命令行工具", "智研", "企业集成服务",
        "云压测", "控制中心", "腾讯云安灯", "腾讯客户端性能分析", "腾讯轻联",
        "地域管理系统", "效能洞察", "腾讯云助手", "检测工具", "集团账号管理",
        "操作审计",
    ],
    "12 云通信与企业服务": [
        "腾讯电子签", "企业微信", "腾讯会议", "腾讯企业邮",
        "腾讯文档", "短信", "邮件推送", "传真", "移动推送",
        "云客服", "腾讯云呼叫中心", "腾讯企点", "企点客服", "腾讯名片",
        "工商注册", "商标注册", "网站设计", "网站建设", "域名注册", "域名交易",
        "增值电信", "号码认证", "电子签章", "在线客服", "在线坐席", "客服工单",
        "ICP备案", "腾讯浏览服务", "腾讯云建站",
    ],
    "13 办公协同": [
        "腾讯会议", "CoDesign设计协作平台", "CoDesign 设计协作平台", "互动白板",
        "腾讯问卷", "腾讯文档", "腾讯HR", "腾讯 HR 助手", "腾讯乐享",
        "低代码平台", "低代码开发平台", "低代码开发平台-1",
        "云管理", "腾讯云管理中心", "企业网盘", "搜狗输入法企业版", "企业移动管理",
        "腾讯云可视化", "腾讯微卡", "腾讯云图数据可视化", "腾讯云微搭低代码",
        "腾讯云微搭低代码-1",
    ],
    "14 微信生态": [
        "微信小程序", "小程序·云开发", "微信小游戏", "Webify", "Web 应用托管",
        "CloudBase Run", "云托管 CloudBase Run", "腾讯云开发",
        "云开发 CloudBase", "云开发 CloudBase-1", "云支付", "微信云支付", "智能增长",
        "小程序消息推送", "微信小程序直播", "微信小程序安全", "微信网关",
        "微瓴物联网类操作系统", "企业微信汽车行业版", "腾讯云静态网站托管",
        "腾讯云小程序平台",
    ],
    "15 物联网": [
        "物联网通信", "物联网开发平台", "TencentOS tiny",
        "LPWA物联网络", "LPWA 物联网络", "物联网智能视频", "实时定位", "智慧零售",
        "优码", "腾讯优码", "物联网市场", "物联网设备身份认证", "车联网 AI 引擎",
        "物联网设备洞察", "腾讯物联网终端操作系统",
    ],
    "16 行业应用": [
        "智能制造协同平台", "云端智造协同平台", "AI临床助手", "AI 临床助手",
        "AI医疗助手", "AI 就医助手", "AI精准预约", "精准预约", "至信链",
        "至信链版权存证", "区块链互操作平台", "区块链可信存证", "区块链可信存证平台",
        "区块链存证", "分布式身份", "碳引擎", "供应链金融", "智慧零售",
        "四力增长平台", "腾讯智慧零售四力增长平台", "旅游大数据平台", "文旅客情大数据",
        "智慧医疗", "智慧医院", "医学影像", "数智医疗影像平台", "数智医疗影像平台-1",
        "医疗内容平台", "医疗报告结构化", "新材料研发平台", "材料研究平台",
        "金融私有云测试平台", "金融专有云开发测试平台", "数字乡村", "腾讯数字农村",
        "能碳工场", "腾讯智慧能源能碳工场", "能源双碳", "腾讯智慧能源数字孪生",
        "腾讯智慧能源连接器", "企业金融平台", "企业金融服务平台",
        "医疗组学平台", "腾讯健康组学平台", "智慧党建", "社交营销", "社会化营销服务",
        "商场 LBS 服务", "智能导诊", "智能预问诊", "家医助手",
        "NGES 医生互动管理套件", "药械会议管理", "药械客户管理", "多渠道营销",
        "传媒云原生移动开发平台", "腾讯云区块链服务平台", "腾讯云区块链保险理赔平台",
        "腾讯云区块链机密计算服务", "腾讯云区块链质押登记平台",
        "智能制造", "智能模型服务", "智能能耗感知", "Web3.0数字营销平台",
        "腾讯云 AIMIS 开放平台", "微瓴同业开放平台", "区块链可信取证",
        "动产质押区块链登记系统", "商业流程服务", "跨链服务平台",
    ],
    "17 服务与营销": [
        "营销自动化", "会员管理", "客户忠诚度管理", "推荐管理", "营销智能推荐",
        "社交客户关系管理", "营销云SCRM", "互动营销", "数字会展", "AB测试", "AB实验平台",
        "行为分析", "会话分析", "用户画像", "画像分析", "增强分析",
        "客户数据平台", "营销活动", "客户关怀平台", "营销云", "营销套件",
        "文本机器人", "外呼机器人", "智能文本质检", "智能语音质检",
        "商通基础", "金融行业-QTrade", "电子行业-腾采通", "印刷行业-网印通",
        "货代行业-货代Q宝", "货代行业-货客通", "RayData 企业版", "RayData 网页版",
    ],
}

TENCENT_CLOUD_CATEGORIES_EN = {
    "01 Compute": [
        "Cloud Virtual Machine", "CVM", "TencentCloud Lighthouse", "Auto Scaling",
        "Cloud Bare Metal", "Cloud Dedicated Cluster", "Cloud Dedicated Zone",
        "BatchCompute", "Cloud GPU Service", "TencentCloud High Performance Computing",
        "TencentCloud Edge Zone", "Tencent Container Registry", "TencentOS Server",
        "TencentCloud Accelerated Computing Optimization Kit", "Tencent Kona",
        "Tencent Cloud OrcaTerm", "Serverless Cloud Function",
        "Serverless Application Center", "Serverless Application Center-1",
        "Serverless HTTP", "Serverless SSR", "Serverless  SSR", "Serverless  SSR-1",
        "FPGA Cloud Computing", "High-Performance Computing Cluster",
    ],
    "02 Container And Middleware": [
        "Tencent Kubernetes Engine", "Elastic Kubernetes Service",
        "Tencent Cloud Kubernetes Service for Edge", "TDMQ for CKafka",
        "TDMQ for RocketMQ", "TDMQ for RabbitMQ", "TDMQ for Pulsar",
        "TDMQ for CMQ", "API Gateway", "Tencent Cloud Mesh",
        "Tencent Cloud Service Engine", "Cloud Native Gateway",
        "Service Registry Center", "Service Governance Center",
        "Tencent Cloud Elastic Microservice", "Tencent Service Framework",
        "Tencent Service Mesh Framework", "Cloud Monitor",
        "Tencent Cloud Application Performance", "Real User Monitoring",
        "Cloud Automated Testing", "Managed Service for Prometheus",
        "TencentCloud Managed Service for Grafana", "Event Bridge",
        "Chaotic Fault Generator", "Cloud Log Service",
    ],
    "03 Storage": [
        "Cloud Object Storage", "LighthouseCOS", "Cloud Block Storage",
        "Cloud File Storage", "Cloud Archive Storage", "Cloud HDFS",
        "Data Lake Accelerator Goose FileSystem", "Cloud Infinite",
        "Image Processing", "Multimedia processing", "Document Service",
        "Image Auditing", "Text Auditing Service", "Media Auditing Service",
        "Audio Auditing Service", "Document Auditing Service", "Content Recognition",
        "Smart Media Hosting", "Migration Service Platform", "Cloud Data Migration",
        "Cloud Storage Gateway", "TStor", "TStor B2000",
        "Extrem Parallel File System", "Intelligent Surveillance Storage",
    ],
    "04 Tencentdb": [
        "Cloud Native Database TDSQL-C", "TencentDB for CynosDB",
        "TDSQL-C for PostgreSQL", "TencentDB for MySQL", "TencentDB for MariaDB",
        "TencentDB for SQL Server", "TencentDB for PostgreSQL", "Lighthouse Database",
        "Tencent Distributed SQL", "Tencent Distributed MySQL", "TencentDB for TBase",
        "HTAP Database TDSQL-H", "TDSQL-H TxLightning", "TencentDB for Redis",
        "TencentDB for MongoDB", "TencentDB for Memcached", "TencentDB for CTSDB",
        "Tcaplus DataBase", "TencentDB for KeeWiDB", "Tencent Cloud VectorDB",
        "Database Appliance TData", "Database Dedicated Cluster",
        "Data Transmission Service", "Database Expert Service", "TencentDB for DBbrain",
        "Database Backup Service", "Database Management Console",
        "Database Distributed Cloud Center",
    ],
    "05 Network": [
        "Cloud Load Balancer", "Virtual Private Cloud", "Elastic Network Interface",
        "NAT Gateway", "Flow Logs", "Anycast Internet Acceleration",
        "Bandwidth Package", "Traffic Package", "Elastic IPv6", "Elastic IP",
        "Private Link", "Direct Connect", "Cloud Connect Network", "VPN Connections",
        "Cloud services of 5G", "Peering Connection", "SD-WAN Access Service",
        "Private DNS", "Intelligent Global Traffic Management", "HttpDNS",
        "Load Master",
    ],
    "06 Cdn And Cloud Communication": [
        "TencentCloud EdgeOne", "Content Delivery Network",
        "Enterprise Content Delivery Network", "Anti-DDoS",
        "Multiple Network Acceleration", "Global Application Acceleration Platform",
        "Edge Computing Machine",
    ],
    "07 Video": [
        "Tencent Real-Time Communication", "Instant Messaging",
        "Tencent Cloud Contact Center", "Voice Message Service",
        "Low-code interactive classroom", "Tencent Real-time Reality Operation",
        "IoT Explorer", "Game Multimedia Engine", "Cloud Streaming Services",
        "Live Video Broadcasting", "Live Camera Broadcasting", "Live Event Broadcasting",
        "Live Video Caster", "Video on Demand", "Cloud Media Engine",
        "TAIDESIGN CREATIVE", "Invision 3D Tour", "Audio and video terminal engine",
        "Voice And Video Calling SDK", "Live streaming SDK", "User Generated Short Video",
        "Tencent Effect SDK", "Player SDK", "Avatar SDK", "Real-time Conference SDK",
        "Media Processing Service", "Media Processing Service for Enterprises",
        "Top Speed Codec", "Intelligent Identification", "Intelligent Auditing",
        "Intelligent Editing", "Game Streaming", "Cloud Virtual Desktop",
        "Cloud Application Rendering", "X-P2P", "TRTC Copilot", "Video creation",
    ],
    "08 Security": [
        "Cloud Firewall", "Security Operations Center", "Web Application Firewall",
        "API Security", "Vulnerability Scan Service", "Network Intrusion Prevention System",
        "Network Traffic Analysis System", "Threat Intelligence X",
        "Threat Intelligence Atom Engine", "Threat Intelligence Attack Surface Management",
        "Security Data Lake", "Cloud Workload Protection", "Tencent Container Security Service",
        "Next generation micro-segmentation", "Data Security Governance Center",
        "Cloud Access Security Broker", "Data Security Platform", "Data Security Audit",
        "Key Management Service", "Secrets Manager", "Cloud Hardware Security Module",
        "Confidential Computing Platform", "Data Mask", "Bastion Host",
        "Cloud Data Coffer Service", "SSL Certificates", "Secure Sockets Layer Pod",
        "Code Signing Certificates", "TencentCloud Digital Credential",
        "Cloud Access Management", "Cloud Identity Governance", "Captcha",
        "Account Security Service", "Business Risk Intelligence", "Traffic Anti-Fraud",
        "Fraud Protection", "Mobile Tencent Protect", "Security Scenario",
        "Breach and Attack Simulation Platform", "Binary Software Composition Analysis",
        "Application Security Development", "Zero Trust Access Control system",
        "Cloud Security Posture Management service", "Application compliance platform",
        "Cybersecurity Attack-Defense Confrontation", "Cybersecurity In Important Period",
        "Customer Identity and Access Management", "Penetration Testing Service",
        "Device Safety", "Managed Security Service", "Mobile Security",
        "Mobile Mini Programs Security", "Identity and Access Management",
        "Incident Response Service", "Tencent Cloud Certificate Authority",
        "Tencent Cloud Certificate Authority-1", "Security Radar",
        "Security of Marketing Phone Number", "Security Expert Service",
        "T-Sec RiskControlEngine",
    ],
    "09 Bigdata": [
        "Elastic MapReduce", "Wedata", "Data Integration", "Data Lake Compute",
        "Stream compute Service", "Oceanus", "TencentDB for ClickHouse",
        "Data Lake Formation", "Elasticsearch Service", "Graph Compute",
        "StreamLIS", "Sparkling", "Data Warehouse Service", "Business Intelligence",
        "Big Data Visualization and Interaction System", "Tencent Cloud Risk Control",
        "Data Classification and Grading", "Data Asset Management and Governance",
        "Privacy Computation", "WeData Data Development Platform", "Federated Learning",
        "Tencent Big Data Suite", "Risk Control Platform", "DataInLong",
    ],
    "10 Artificial Intelligence And Machine Learning": [
        "TencentCloud TI Platform", "Tencent Hunyuan", "Automatic Speech Recognition",
        "Text To Speech", "Natural Language Processing", "Tencent Machine Translation",
        "Tencent Simultaneous Interpretation", "Face Recognition", "Face Effects",
        "Face Fusion", "Body Analysis", "Image Recognition", "Image Processing",
        "Optical Character Recognition", "Smart Document OCR", "Intelligent Structure Data",
        "Content Moderation System", "Video Moderation System", "Text Moderation System",
        "Audio Moderation System", "Image Moderation System", "Smart Conversation Analysis",
        "Music Tag Recognition", "Sentiment Analysis", "Tencent Knowledge Graph",
        "conversation Robot", "Intelligent Guidance", "customer service chatbot",
        "intelligent outbound voicebot", "intelligent speech quality assurance",
        "intelligent massage quality assurance", "Smart Oral Evaluation",
        "Intelligent Hardware AI Voice Assistant", "Intelligent Media Label Detection",
        "Intelligent Pre-Consultation", "Family Doctor Assistant",
        "Digital and Intelligent Medical Imaging Platform", "Image Creation",
        "Image Learning", "IP Virtual Human", "English Composition Correction",
        "Homework Correction-Math", "Text To Speech Workshop",
    ],
    "11 Development And Operation": [
        "CODING DevOps", "CODING Continuous Integration", "CODING Continuous Deployment",
        "CODING Artifact Repositories", "CODING Test Management", "CODING Project Management",
        "CODING Insight", "Cloud Studio", "TencentCloud Automation Tools",
        "Tencent Infrastructure Automation for Terraform", "Tencent Cloud Advisor",
        "CloudConfig", "CloudAudit", "Tencent Resource", "Tencent Cloud Enterprise Organization",
        "Health Dashboard", "Message Center", "Tag", "Cost Management", "Code Analysis",
        "Tencent Cloud Andon", "WeTest", "Cloud Hosting Cluster", "Region Management System",
        "Application Programming Interface", "Expert Compatibility Testing",
        "Detection Tools", "Hyper Application Inventor", "Tencent Agile Product Development",
        "Performance Test Service", "Standard Compatibility Testing", "Remote Debugging",
        "TCCLI",
    ],
    "12 Enterprise And Communication": [
        "Tencent Electronic Signature", "Tencent WeCom", "Tencent Meeting",
        "Tencent Enterprise Mail", "Tencent Docs", "Short Message Service",
        "Email Service", "Fax Platform", "Tencent Push Notification Service",
        "Tencent Customer Service", "Tencent QiDian", "Tencent Wecard",
        "Business Registration", "Trademark Registering", "Website Design Service",
        "Domain Name Registration", "Domain Name Transaction", "Telecom value-added",
        "Number Verification Service", "Online Customer Service", "Customer Service Ticket",
        "Corporate QQ for Freight", "Corporate QQ for Interntational Trade and Logistics",
        "Electronic Trade Customer Relationship Management", "Domain registration",
        "Tencent Browsing Service", "Enterprise Integration Service",
        "Next Generation Engagement Suite", "NGES Customer Relationship Management",
        "Quick Application Performance Monitor", "Tencent Cloud Assistant",
        "Print Communication Network", "Tencent E-Sign Service Overview",
        "Tencent E-Sign Service Overview-1",
    ],
    "13 Office Collaboration": [
        "Tencent Meeting", "CoDesign Collaborative Platform for Design",
        "Tencent Interactive Whiteboard", "Tencent Survey", "Tencent Docs",
        "Tencent HR Management", "Low Code Platform", "Low Code-1",
        "Cloud Management Product", "Tencent Cloud Enterprise Drive",
        "Enterprise Mobility Management", "Sogou Input Method For Business",
        "Media Cloudnative Mobile Platform", "Tencent Cloud Visualization",
        "Mobile Office Platform", "lexiang",
    ],
    "14 Wechat Ecosystem": [
        "WeChat Mini Programs", "WeChat Mini Games", "CloudBase Webify",
        "Tencent CloudBase Run", "Tencent Cloud Pages", "Cloud Pay",
        "TencentCloud Smart Growth Kit", "Tencent Cloud Base", "WeilingWith",
        "Messenger Platform", "Tencent Cloud Mini Program Platform",
    ],
    "15 Internet Of Things": [
        "IoT Hub", "IoT Explorer", "TencentOS tiny", "LPWA IoT Hub", "IoT Video",
        "Real Time Location", "Smart Retail", "Tencent Youma",
        "Internet of Things Hub", "Internet of Things Video", "IoT Insight",
    ],
    "16 Industry": [
        "Cloud Intelligent Manufacturing Collaboration Platform", "AI Clinical Assistant",
        "AI Medical Assistant", "AI Precision Appointment", "ZhiXinChain",
        "ZhiXinChain Copyright Deposit", "Blockchain Interoperate Service Platform",
        "Blockchain Trusted Obtain Evidence", "TencentCloud Decentralized Identity",
        "TencentCloud Carbon Engine", "Tencent Supply Chain Finance", "Smart Retail",
        "Tencent Smart Retail Four Forces Growth Platform", "tourism bigdata platform",
        "BPaaS", "Intelligent EnergyAwareness", "Intelligent Manufacture",
        "Intelligent Model Service", "Tencent Blockchain as a Service",
        "Tencent Blockchain Pledge Registration", "Tencent Cloud House",
        "Tencent Digital Countryside", "Tencent EnerCarbon Studio", "Tencent EnerTwin",
        "Tencent Enterprise Fintech Platform", "Tencent HealthCare Omics Platform",
        "Tencent Healthcare Administrator", "Smart Party Building", "Social Marketing Software",
        "mall lbs", "Medical Content Platform", "Medical Report Structured",
        "Materials Research Platform", "Financial Private Cloud Research and Design Test Platform",
        "Tencent AIMIS Open Platform", "Tencent Cloud Blockchain Confidential Computing",
    ],
    "17 Service Marketing": [
        "Marketing Automation", "Loyalty Management", "Recommend Management",
        "Social Customer Relationship Management", "Interactive Marketing Platform",
        "Digital Exhibition", "A/Btest", "Behavior Analytics", "ConversationalAnalysis",
        "Profile Analytics", "Augmented Analytics", "Customer Data Platform",
        "Multi-Channel Marketing", "Tencent Reassurance User Operation Platform",
        "NGES Events", "Brand Manager Assistant", "Business Connect",
        "Company Payment Distributor Platform", "Engagement Suite", "QTrade",
        "RayData Plus", "RayDataWeb-Public", "A:Btest",
    ],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_name(name: str) -> str:
    """
    Normalize product name for matching.
    - Replace NBSP with regular space
    - Remove extra spaces
    - Convert to lowercase
    """
    # Replace NBSP with regular space
    name = name.replace(NBSP, ' ')
    # Remove extra spaces and strip
    name = ' '.join(name.split())
    return name.lower().strip()


def normalize_filename(filename: str) -> str:
    """
    Normalize filename by replacing NBSP with regular space.
    """
    return filename.replace(NBSP, ' ')


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def word_overlap_score(s1: str, s2: str) -> float:
    """Calculate word overlap score between two strings."""
    words1 = set(normalize_name(s1).split())
    words2 = set(normalize_name(s2).split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0


# =============================================================================
# PPTX EXTRACTION
# =============================================================================

def extract_text_from_pptx(pptx_path: str) -> dict:
    """
    Extract text content from a PPTX file.
    Returns a dictionary mapping slide numbers to list of text content.
    """
    slides_text = {}
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Extract PPTX (it's a ZIP file)
        with zipfile.ZipFile(pptx_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
        
        slides_dir = Path(tmp_dir) / 'ppt' / 'slides'
        if not slides_dir.exists():
            return slides_text
        
        # Parse each slide
        for slide_file in sorted(slides_dir.glob('slide*.xml')):
            slide_num = int(re.search(r'slide(\d+)\.xml', slide_file.name).group(1))
            
            try:
                tree = ET.parse(slide_file)
                root = tree.getroot()
                
                # Extract all text elements
                texts = []
                for elem in root.iter():
                    if elem.tag.endswith('}t'):  # Text element
                        if elem.text:
                            texts.append(elem.text.strip())
                
                slides_text[slide_num] = texts
            except Exception as e:
                print(f"Warning: Error parsing {slide_file.name}: {e}")
    
    return slides_text


def parse_categories_from_pptx(pptx_path: str, language: str = 'zh') -> dict:
    """
    Parse product categories from PPTX content.
    
    This function tries to identify category headers and products within each slide.
    Typically, the first text element is the category name, followed by product names.
    """
    slides_text = extract_text_from_pptx(pptx_path)
    
    # Categories extracted from PPTX
    categories = {}
    current_category = None
    category_index = 1
    
    # Common category patterns (Chinese and English)
    category_patterns_zh = [
        r'计算', r'容器', r'存储', r'数据库', r'网络', r'CDN', r'视频',
        r'安全', r'大数据', r'人工智能', r'开发', r'运维', r'通信',
        r'办公', r'微信', r'物联网', r'行业', r'营销', r'云通信',
    ]
    category_patterns_en = [
        r'Compute', r'Container', r'Storage', r'Database', r'Network',
        r'CDN', r'Video', r'Security', r'Big\s*Data', r'AI', r'Machine Learning',
        r'Development', r'Operation', r'Communication', r'Office',
        r'WeChat', r'IoT', r'Industry', r'Marketing',
    ]
    
    patterns = category_patterns_zh if language == 'zh' else category_patterns_en
    
    for slide_num in sorted(slides_text.keys()):
        texts = slides_text[slide_num]
        if not texts:
            continue
        
        # Check if first text is a category header
        first_text = texts[0]
        is_category = any(re.search(p, first_text, re.IGNORECASE) for p in patterns)
        
        if is_category:
            # Create category name with index
            category_name = f"{category_index:02d} {first_text}"
            categories[category_name] = []
            current_category = category_name
            category_index += 1
            
            # Remaining texts are products
            categories[category_name].extend(texts[1:])
        elif current_category:
            # Add all texts to current category
            categories[current_category].extend(texts)
    
    return categories


# =============================================================================
# SVG FILE HANDLING
# =============================================================================

def get_icon_files(icons_dir: Path, extension: str = 'svg') -> dict:
    """
    Get all icon files in the icons directory.
    Returns a dictionary mapping normalized names to file paths.
    
    Args:
        icons_dir: Path to the icons directory
        extension: File extension to look for (e.g., 'svg', 'png')
    """
    icon_files = {}
    for f in icons_dir.glob(f"*.{extension}"):
        if f.is_file():
            norm_name = normalize_name(f.stem)
            icon_files[norm_name] = f
    return icon_files


def get_svg_files(icons_dir: Path) -> dict:
    """
    Get all SVG files in the icons directory.
    Returns a dictionary mapping normalized names to file paths.
    """
    return get_icon_files(icons_dir, 'svg')


def find_best_match(product_name: str, svg_files: dict, threshold: float = 0.6) -> Path:
    """
    Find the best matching SVG file for a product name.
    Uses multiple matching strategies:
    1. Exact match (normalized)
    2. Exact stem match (without -1, -2 suffixes)
    3. Fuzzy match with similarity score
    4. Word overlap match
    """
    norm_product = normalize_name(product_name)
    
    # Strategy 1: Exact match
    if norm_product in svg_files:
        return svg_files[norm_product]
    
    # Strategy 2: Match without version suffix (-1, -2, etc.)
    base_product = re.sub(r'-\d+$', '', norm_product)
    if base_product != norm_product and base_product in svg_files:
        return svg_files[base_product]
    
    # Strategy 3 & 4: Fuzzy and word overlap matching
    best_match = None
    best_score = 0
    
    for svg_name, svg_path in svg_files.items():
        # Skip already matched files (different scoring)
        base_svg = re.sub(r'-\d+$', '', svg_name)
        
        # Similarity score
        sim_score = similarity_score(norm_product, svg_name)
        
        # Word overlap score
        word_score = word_overlap_score(norm_product, svg_name)
        
        # Combined score (weighted average)
        combined_score = 0.6 * sim_score + 0.4 * word_score
        
        # Bonus for containing match
        if norm_product in svg_name or svg_name in norm_product:
            combined_score += 0.3
        
        # Bonus for base name match
        if base_product == base_svg or base_product in base_svg or base_svg in base_product:
            combined_score += 0.2
        
        if combined_score > best_score and combined_score >= threshold:
            best_score = combined_score
            best_match = svg_path
    
    return best_match


# =============================================================================
# MAIN ORGANIZATION FUNCTION
# =============================================================================

def organize_icons(icons_dir: str, categories: dict, dry_run: bool = False, extension: str = 'svg') -> tuple:
    """
    Organize icon files into category directories.
    
    Args:
        icons_dir: Path to the icons directory
        categories: Dictionary mapping category names to list of product names
        dry_run: If True, only show what would be done without moving files
        extension: File extension to organize (e.g., 'svg', 'png')
    
    Returns:
        Tuple of (moved_files set, remaining_files list)
    """
    icons_dir = Path(icons_dir)
    icon_files = get_icon_files(icons_dir, extension)
    print(f"Found {len(icon_files)} {extension.upper()} files to organize")
    print(f"Categories: {len(categories)}")
    
    moved_files = set()
    unmatched_products = []
    
    for category, products in categories.items():
        category_dir = icons_dir / category
        
        # Create category directory
        if not dry_run:
            category_dir.mkdir(exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Category: {category}")
        print(f"{'='*60}")
        
        matched_count = 0
        for product in products:
            icon_path = find_best_match(product, icon_files)
            
            if icon_path and icon_path not in moved_files:
                # Normalize the filename (replace NBSP with regular space)
                new_filename = normalize_filename(icon_path.name)
                dest_path = category_dir / new_filename
                
                if icon_path.exists():
                    if not dry_run:
                        shutil.move(str(icon_path), str(dest_path))
                    moved_files.add(icon_path)
                    matched_count += 1
                    print(f"  ✓ {new_filename}")
            else:
                if icon_path in moved_files:
                    pass  # Already moved, skip silently
                else:
                    unmatched_products.append((category, product))
        
        print(f"  Matched: {matched_count}/{len(products)} products")
    
    # Check remaining files
    remaining_icons = [f for f in icons_dir.glob(f"*.{extension}") if f.is_file()]
    
    # Report results
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total {extension.upper()} files found: {len(icon_files)}")
    print(f"Files moved: {len(moved_files)}")
    print(f"Files remaining: {len(remaining_icons)}")
    
    if unmatched_products:
        print(f"\nUnmatched products ({len(unmatched_products)}):")
        # Show unique unmatched products
        shown = set()
        for cat, prod in unmatched_products:
            if prod not in shown:
                print(f"  - {prod}")
                shown.add(prod)
                if len(shown) >= 20:
                    break
        if len(unmatched_products) > 20:
            print(f"  ... and {len(set(p for _, p in unmatched_products)) - 20} more unique products")
    
    if remaining_icons:
        print(f"\nRemaining {extension.upper()} files ({len(remaining_icons)}):")
        for f in sorted(remaining_icons)[:50]:
            print(f"  - {f.name}")
        if len(remaining_icons) > 50:
            print(f"  ... and {len(remaining_icons) - 50} more")
    
    return moved_files, remaining_icons


def organize_remaining_files(icons_dir: str, categories: dict, 
                            remaining_mapping: dict = None, dry_run: bool = False,
                            extension: str = 'svg') -> tuple:
    """
    Second pass: organize remaining files using direct filename mapping.
    
    Args:
        icons_dir: Path to the icons directory
        categories: Dictionary mapping category names to list of product names
        remaining_mapping: Direct filename to category mapping for edge cases
        dry_run: If True, only show what would be done
        extension: File extension to organize (e.g., 'svg', 'png')
    
    Returns:
        Tuple of (moved_count, remaining_count)
    """
    icons_dir = Path(icons_dir)
    remaining_icons = list(icons_dir.glob(f"*.{extension}"))
    
    if not remaining_icons:
        print(f"No remaining {extension.upper()} files to organize.")
        return 0, 0
    
    print(f"\n{'='*60}")
    print(f"SECOND PASS: Organizing {len(remaining_icons)} remaining files")
    print(f"{'='*60}")
    
    moved_count = 0
    
    # Build reverse mapping: product name -> category
    product_to_category = {}
    for category, products in categories.items():
        for product in products:
            norm_product = normalize_name(product)
            product_to_category[norm_product] = category
    
    for icon_path in remaining_icons:
        filename = icon_path.name
        norm_filename = normalize_name(icon_path.stem)
        
        # Check direct mapping first
        if remaining_mapping and filename in remaining_mapping:
            category = remaining_mapping[filename]
        elif remaining_mapping:
            # Try with normalized filename
            norm_key = normalize_filename(filename)
            if norm_key in remaining_mapping:
                category = remaining_mapping[norm_key]
            else:
                category = None
        else:
            category = None
        
        # Try to match by partial name
        if not category:
            for prod_name, cat in product_to_category.items():
                if prod_name in norm_filename or norm_filename in prod_name:
                    category = cat
                    break
        
        if category:
            category_dir = icons_dir / category
            if category_dir.exists():
                new_filename = normalize_filename(filename)
                dest_path = category_dir / new_filename
                
                if not dry_run:
                    shutil.move(str(icon_path), str(dest_path))
                print(f"  ✓ {new_filename} -> {category}")
                moved_count += 1
    
    remaining_count = len(list(icons_dir.glob(f"*.{extension}")))
    print(f"\nMoved in second pass: {moved_count}")
    print(f"Still remaining: {remaining_count}")
    
    return moved_count, remaining_count


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Organize cloud product icon files into categorized folders.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize Chinese SVG icons using built-in categories
  python3 organize_icons.py --icons-dir ./icons/zh --language zh

  # Organize English icons with dry run
  python3 organize_icons.py --icons-dir ./icons/en --language en --dry-run

  # Organize PNG icons
  python3 organize_icons.py --icons-dir ./icons/en --language en --extension png

  # Use custom categories from PPTX file
  python3 organize_icons.py --icons-dir ./icons --pptx ./icons.pptx --language zh

  # Use custom categories from JSON file
  python3 organize_icons.py --icons-dir ./icons --categories-file ./categories.json
        """
    )
    parser.add_argument('--icons-dir', required=True,
                        help='Path to the icons directory containing icon files')
    parser.add_argument('--language', choices=['zh', 'en'], default='zh',
                        help='Language for built-in category names (zh=Chinese, en=English)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without actually moving files')
    parser.add_argument('--pptx', dest='pptx_path',
                        help='Path to PPTX file to extract categories from')
    parser.add_argument('--categories-file',
                        help='Path to custom categories JSON file')
    parser.add_argument('--extension', default='svg',
                        help='File extension to organize (default: svg)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Validate icons directory
    icons_dir = Path(args.icons_dir)
    if not icons_dir.exists():
        print(f"Error: Icons directory does not exist: {icons_dir}")
        return 1
    
    # Determine categories source
    if args.categories_file:
        print(f"Loading categories from: {args.categories_file}")
        with open(args.categories_file, 'r', encoding='utf-8') as f:
            categories = json.load(f)
    elif args.pptx_path:
        print(f"Extracting categories from PPTX: {args.pptx_path}")
        categories = parse_categories_from_pptx(args.pptx_path, args.language)
        if not categories:
            print("Warning: Could not extract categories from PPTX, using built-in categories")
            categories = TENCENT_CLOUD_CATEGORIES_ZH if args.language == 'zh' else TENCENT_CLOUD_CATEGORIES_EN
    else:
        print(f"Using built-in {args.language.upper()} categories")
        categories = TENCENT_CLOUD_CATEGORIES_ZH if args.language == 'zh' else TENCENT_CLOUD_CATEGORIES_EN
    
    # Run organization
    mode_str = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{mode_str}Organizing icons in: {icons_dir}")
    
    extension = args.extension.lstrip('.')
    
    # First pass
    moved_files, remaining = organize_icons(str(icons_dir), categories, args.dry_run, extension)
    
    # Second pass if there are remaining files
    if remaining and not args.dry_run:
        print("\nRunning second pass for remaining files...")
        organize_remaining_files(str(icons_dir), categories, dry_run=args.dry_run, extension=extension)
    
    # Final summary
    final_remaining = list(icons_dir.glob(f"*.{extension}")) if not args.dry_run else remaining
    if not final_remaining:
        print(f"\n✅ All {extension.upper()} files have been organized successfully!")
    else:
        print(f"\n⚠️  {len(final_remaining)} files could not be automatically categorized.")
        print("Please review and manually categorize these files.")
    
    return 0


if __name__ == "__main__":
    exit(main())
