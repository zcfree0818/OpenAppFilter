#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenAppFilter 中英文全量特征库智能合并与 XTEA-CTR 加密工具
"""
import os
import sys
import struct
import zlib
from collections import OrderedDict

# 官方固定的 XTEA 32位加密密钥 (来自 fwx_rule.c / appfilter 模块)
KEY = [0x8f4c29a1, 0x73b6d502, 0xc14e87f3, 0x2ad95b60]
DELTA = 0x9E3779B9

# 11个冲突英文应用的新 AppID 映射 (分配到绝对未被占用的安全区)
CONFLICT_MAPPING = {
    3101: (3201, "YouTube"),
    3103: (3203, "NetFlix"),
    3104: (3204, "Vimeo"),
    3105: (3205, "DailyMotion"),
    3106: (3206, "Hulu"),
    8103: (8203, "Yahoo"),
    8104: (8204, "Apple"),
    8110: (8210, "Reddit"),
    8111: (8211, "Outlook"),
    8132: (8232, "Weather"),
    8135: (8235, "Microsoft"),
}

def xtea_encrypt_block(v0, v1, key):
    sum_val = 0
    for _ in range(32):
        v0 = (v0 + ((((v1 << 4) ^ (v1 >> 5)) + v1) ^ (sum_val + key[sum_val & 3]))) & 0xFFFFFFFF
        sum_val = (sum_val + DELTA) & 0xFFFFFFFF
        v1 = (v1 + ((((v0 << 4) ^ (v0 >> 5)) + v0) ^ (sum_val + key[(sum_val >> 11) & 3]))) & 0xFFFFFFFF
    return v0, v1

def xtea_ctr_crypt(data: bytes, nonce: int, key=KEY) -> bytes:
    out = bytearray()
    num_blocks = (len(data) + 7) // 8
    for block_idx in range(num_blocks):
        counter = (nonce + block_idx) & 0xFFFFFFFFFFFFFFFF
        v0 = counter & 0xFFFFFFFF
        v1 = (counter >> 32) & 0xFFFFFFFF
        ks0, ks1 = xtea_encrypt_block(v0, v1, key)
        ks = struct.pack('<II', ks0, ks1)
        chunk = data[block_idx*8 : (block_idx+1)*8]
        for b, k in zip(chunk, ks[:len(chunk)]):
            out.append(b ^ k)
    return bytes(out)

def build_encrypted_feature_bin(plaintext_bytes: bytes, nonce: int = 0xf583e643d327685f) -> bytes:
    """按照 OpenAppFilter 标准 FWXB 头部封装并加密二进制特征库"""
    plain_len = len(plaintext_bytes)
    crc = zlib.crc32(plaintext_bytes) & 0xFFFFFFFF
    ciphertext = xtea_ctr_crypt(plaintext_bytes, nonce)
    header = struct.pack('<4sBBHIIQ', b'FWXB', 1, 1, 24, plain_len, crc, nonce)
    return header + ciphertext

def parse_feature_file(filepath):
    """解析特征库文件为结构化数据"""
    classes = OrderedDict() # cid: (code, name, [apps])
    current_cid = None
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith('#class'):
                parts = line_str.split(None, 3)
                code = parts[1]
                cid = int(parts[2])
                name = parts[3] if len(parts) > 3 else code
                if cid not in classes:
                    classes[cid] = {'code': code, 'name': name, 'apps': []}
                current_cid = cid
            elif not line_str.startswith('#'):
                if '~' in line_str and ':[' in line_str:
                    app_id_str, rest = line_str.split('~', 1)
                    app_name, rule_str = rest.split(':[', 1)
                    rule_str = rule_str.rstrip(']')
                    aid = int(app_id_str)
                    if current_cid is not None and current_cid in classes:
                        classes[current_cid]['apps'].append({
                            'id': aid,
                            'name': app_name,
                            'rules': rule_str,
                            'orig_line': line_str
                        })
    return classes

def merge_features(cn_path, en_path, out_plain_path, out_bin_path):
    print(f"[*] 开始解析中文特征库: {cn_path}")
    cn_classes = parse_feature_file(cn_path)
    print(f"[*] 开始解析英文特征库: {en_path}")
    en_classes = parse_feature_file(en_path)
    
    # 统计已有 AppID
    existing_ids = set()
    total_cn_apps = 0
    for cid, cinfo in cn_classes.items():
        for app in cinfo['apps']:
            existing_ids.add(app['id'])
            total_cn_apps += 1
            
    print(f"[+] 中文库解析完毕: 共 {len(cn_classes)} 个分类, {total_cn_apps} 款应用")
    
    # 合并英文库应用
    added_en_apps = 0
    remapped_apps = 0
    for cid, cinfo in en_classes.items():
        target_cid = cid
        if target_cid not in cn_classes:
            cn_classes[target_cid] = {'code': cinfo['code'], 'name': cinfo['name'], 'apps': []}
            
        for app in cinfo['apps']:
            aid = app['id']
            aname = app['name']
            arules = app['rules']
            
            # 检查是否有 ID 冲突
            if aid in existing_ids:
                if aid in CONFLICT_MAPPING:
                    new_aid, mapped_name = CONFLICT_MAPPING[aid]
                    print(f"  [-] 解决 ID 冲突: 英文应用 [{aid}] {aname} -> 重映射至 [{new_aid}] {mapped_name}")
                    aid = new_aid
                    remapped_apps += 1
                else:
                    # 自动递增寻找空闲 ID
                    base_id = (cid * 1000) + 800
                    while base_id in existing_ids:
                        base_id += 1
                    print(f"  [-] 自动重新分配冲突 ID: [{app['id']}] {aname} -> [{base_id}]")
                    aid = base_id
                    remapped_apps += 1
                    
            existing_ids.add(aid)
            cn_classes[target_cid]['apps'].append({
                'id': aid,
                'name': aname,
                'rules': arules,
                'orig_line': f"{aid}~{aname}:[{arules}]"
            })
            added_en_apps += 1

    print(f"[+] 英文应用合并完毕: 新增 {added_en_apps} 款应用 (其中 {remapped_apps} 款自动重映射避免冲突)")
    
    # 按照分类和 AppID 排序生成明文
    lines = [
        "#version 26.11.08",
        "#format v4.0",
        "#type 0",
        "#free 1",
        "#Author: destan19 & AI-Enhanced Bilingual Merger",
        "#Copyright(C) www.openappfilter.com All Rights Reserved.",
        "#Website:www.openappfilter.com www.fanchmwrt.com",
        "#id name:[proto;sport;dport;host url;request;dict;search str;ignore]",
        ""
    ]
    
    total_merged_apps = 0
    for cid, cinfo in sorted(cn_classes.items()):
        lines.append(f"#class {cinfo['code']} {cid} {cinfo['name']}")
        # 按照 AppID 升序排序，保证特征库清晰整齐
        sorted_apps = sorted(cinfo['apps'], key=lambda x: x['id'])
        for app in sorted_apps:
            lines.append(f"{app['id']}~{app['name']}:[{app['rules']}]")
            total_merged_apps += 1
        lines.append("") # 分类间空行
        
    plain_content = "\n".join(lines).strip() + "\n"
    plain_bytes = plain_content.encode('utf-8')
    
    with open(out_plain_path, 'wb') as f:
        f.write(plain_bytes)
    print(f"[+] 成功写入合并后明文特征库: {out_plain_path} (总计 {total_merged_apps} 款应用, 大小: {len(plain_bytes)} 字节)")
    
    # 加密生成 feature.bin
    bin_bytes = build_encrypted_feature_bin(plain_bytes)
    with open(out_bin_path, 'wb') as f:
        f.write(bin_bytes)
    print(f"[+] 成功生成标准 XTEA-CTR 加密二进制特征库: {out_bin_path} (大小: {len(bin_bytes)} 字节)")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, '..'))
    
    cn_file = os.path.join(root_dir, 'feature_cn_plain.txt')
    en_file = os.path.join(root_dir, 'feature_en_plain.txt')
    out_plain = os.path.join(root_dir, 'feature_merged_plain.txt')
    out_bin = os.path.join(root_dir, 'feature.bin')
    
    merge_features(cn_file, en_file, out_plain, out_bin)
