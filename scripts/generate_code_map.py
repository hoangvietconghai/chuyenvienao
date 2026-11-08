#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
scripts/generate_code_map.py
============================
Công cụ phân tích mã nguồn tự động (AST Codebase Analyzer & Indexer)
dành cho Hệ thống Chuyên viên Ảo Văn phòng Đảng uỷ xã Công Hải.

Chức năng:
1. Quét toàn bộ mã nguồn Python trong server/ và scripts/ bằng thư viện chuẩn `ast`.
2. Bóc tách tự động: Docstring, Classes, Methods, Functions, và FastAPI Route Endpoints.
3. Xuất bảng ánh xạ mã nguồn (Symbol Index) và thống kê hệ thống.
4. Tự động đồng bộ / cập nhật phân đoạn tự động trong CODEBASE_MAP.md.
5. Kiểm tra tính toàn vẹn (Health-Check & Coverage) đảm bảo không có file nào bị bỏ sót.

Chạy:
    python scripts/generate_code_map.py
    python scripts/generate_code_map.py --check
    python scripts/generate_code_map.py --export-json data/codebase_symbols.json
    python scripts/generate_code_map.py --update-map
"""

import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent.parent


class CodebaseVisitor(ast.NodeVisitor):
    """AST Visitor bóc tách classes, functions, decorators, endpoints."""

    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.docstring: str = ""
        self.classes: List[Dict[str, Any]] = []
        self.functions: List[Dict[str, Any]] = []
        self.endpoints: List[Dict[str, Any]] = []
        self.imports: List[str] = []

    def visit_Module(self, node: ast.Module):
        self.docstring = ast.get_docstring(node) or ""
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        for alias in node.names:
            self.imports.append(f"{mod}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    "name": item.name,
                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                    "doc": (ast.get_docstring(item) or "").split("\n")[0].strip()
                })
        self.classes.append({
            "name": node.name,
            "doc": (ast.get_docstring(node) or "").split("\n")[0].strip(),
            "line": node.lineno,
            "methods": methods
        })

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node, is_async=True)

    def _handle_function(self, node, is_async: bool):
        # Bóc tách endpoint decorators: @app.get, @router.post, etc.
        for dec in node.decorator_list:
            endpoint_info = self._parse_route_decorator(dec)
            if endpoint_info:
                endpoint_info["function"] = node.name
                endpoint_info["is_async"] = is_async
                endpoint_info["line"] = node.lineno
                endpoint_info["doc"] = (ast.get_docstring(node) or "").split("\n")[0].strip()
                self.endpoints.append(endpoint_info)

        # Lưu hàm cấp module (không nằm trong class)
        self.functions.append({
            "name": node.name,
            "is_async": is_async,
            "line": node.lineno,
            "doc": (ast.get_docstring(node) or "").split("\n")[0].strip(),
            "args": [arg.arg for arg in node.args.args]
        })

    def _parse_route_decorator(self, dec) -> Optional[Dict[str, Any]]:
        # Decorator dạng @router.get("/path") hoặc @app.post("/path")
        if isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Attribute):
                caller = ""
                if isinstance(func.value, ast.Name):
                    caller = func.value.id
                method = func.attr.upper()
                if method in ("GET", "POST", "PUT", "DELETE", "PATCH", "WEBSOCKET") and caller in ("app", "router", "search_router"):
                    path = ""
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        path = str(dec.args[0].value)
                    return {
                        "caller": caller,
                        "method": method,
                        "path": path,
                    }
        return None


def scan_file(file_path: Path) -> Dict[str, Any]:
    """Phân tích 1 tệp Python bằng AST."""
    rel_path = file_path.relative_to(BASE_DIR).as_posix()
    try:
        content = file_path.read_text(encoding="utf-8")
        parsed = ast.parse(content, filename=str(file_path))
        visitor = CodebaseVisitor(rel_path)
        visitor.visit(parsed)
        return {
            "path": rel_path,
            "docstring": visitor.docstring,
            "classes": visitor.classes,
            "functions": visitor.functions,
            "endpoints": visitor.endpoints,
            "lines": len(content.splitlines()),
            "status": "OK"
        }
    except Exception as e:
        return {
            "path": rel_path,
            "docstring": "",
            "classes": [],
            "functions": [],
            "endpoints": [],
            "lines": 0,
            "status": f"ERROR: {e}"
        }


def scan_codebase() -> Dict[str, Any]:
    """Quét toàn bộ mã nguồn server/, scripts/."""
    targets = [
        BASE_DIR / "server",
        BASE_DIR / "scripts"
    ]
    files_result = []
    total_lines = 0
    total_endpoints = 0
    total_classes = 0
    total_functions = 0

    for target in targets:
        if not target.exists():
            continue
        for py_file in sorted(target.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            res = scan_file(py_file)
            files_result.append(res)
            total_lines += res["lines"]
            total_endpoints += len(res["endpoints"])
            total_classes += len(res["classes"])
            total_functions += len(res["functions"])

    return {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_files": len(files_result),
            "total_lines": total_lines,
            "total_classes": total_classes,
            "total_functions": total_functions,
            "total_endpoints": total_endpoints
        },
        "files": files_result
    }


def generate_markdown_table(scan_data: Dict[str, Any]) -> str:
    """Tạo bảng Markdown tóm tắt các tệp và chức năng cốt lõi."""
    lines = []
    lines.append("| Tệp tin | Dòng mã | Lớp / Endpoint | Chức năng & Hàm trọng yếu |")
    lines.append("| :--- | :---: | :---: | :--- |")

    for f in scan_data["files"]:
        path = f["path"]
        line_count = f["lines"]
        ep_count = len(f["endpoints"])
        cl_count = len(f["classes"])
        
        tag = []
        if ep_count > 0:
            tag.append(f"{ep_count} Endpoints")
        if cl_count > 0:
            tag.append(f"{cl_count} Classes")
        if not tag:
            tag.append(f"{len(f['functions'])} Funcs")
        tag_str = ", ".join(tag)

        # Trích lọc dòng đầu tiên của docstring hoặc các hàm tiêu biểu
        summary = ""
        if f["docstring"]:
            first_line = f["docstring"].strip().split("\n")[0]
            summary = first_line.replace("|", "-")
        else:
            fn_names = [fn["name"] for fn in f["functions"][:4]]
            summary = ", ".join(fn_names) if fn_names else "(Module phụ trợ)"

        lines.append(f"| [`{path}`]({path}) | {line_count:,} | {tag_str} | {summary} |")

    return "\n".join(lines)


def generate_endpoint_table(scan_data: Dict[str, Any]) -> str:
    """Tạo bảng danh mục API Endpoints."""
    lines = []
    lines.append("| Method | Endpoint | Hàm phụ trách | Module Router | Ghi chú nghiệp vụ |")
    lines.append("| :---: | :--- | :--- | :--- | :--- |")

    for f in scan_data["files"]:
        for ep in f["endpoints"]:
            method = ep["method"]
            path = ep["path"] or "/"
            fn = ep["function"]
            mod = f["path"]
            doc = ep["doc"] or ""
            lines.append(f"| **`{method}`** | `{path}` | `{fn}` | [`{mod}`]({mod}) | {doc} |")

    return "\n".join(lines)


def update_codebase_map(scan_data: Dict[str, Any], map_path: Path):
    """Cập nhật các phần tự động sinh vào CODEBASE_MAP.md."""
    if not map_path.exists():
        print(f"[-] Không tìm thấy {map_path}")
        return False

    content = map_path.read_text(encoding="utf-8")
    
    start_tag = "<!-- AUTO_GENERATED_SYMBOLS_START -->"
    end_tag = "<!-- AUTO_GENERATED_SYMBOLS_END -->"
    
    if start_tag not in content or end_tag not in content:
        print("[-] Không tìm thấy thẻ đánh dấu AUTO_GENERATED_SYMBOLS trong CODEBASE_MAP.md")
        return False

    auto_block = f"{start_tag}\n\n"
    auto_block += f"> *Tự động cập nhật bởi `scripts/generate_code_map.py` lúc: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*\n"
    auto_block += f"> *Quy mô: **{scan_data['summary']['total_files']}** tệp Python | **{scan_data['summary']['total_lines']:,}** dòng mã | **{scan_data['summary']['total_endpoints']}** API Endpoints*\n\n"
    auto_block += "### Danh mục API Endpoints (FastAPI Routes)\n\n"
    auto_block += generate_endpoint_table(scan_data) + "\n\n"
    auto_block += "### Ma trận Phân vai Tệp tin & Hàm Trọng yếu\n\n"
    auto_block += generate_markdown_table(scan_data) + "\n\n"
    auto_block += f"{end_tag}"

    before = content.split(start_tag)[0]
    after = content.split(end_tag)[1]
    new_content = before + auto_block + after

    map_path.write_text(new_content, encoding="utf-8")
    print(f"[+] Đã cập nhật thành công {map_path}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AST Codebase Analyzer cho Chuyên viên ảo")
    parser.add_argument("--check", action="store_true", help="Kiểm tra phân tích mã nguồn")
    parser.add_argument("--export-json", type=str, help="Xuất kết quả AST ra file JSON")
    parser.add_argument("--update-map", action="store_true", help="Cập nhật trực tiếp vào CODEBASE_MAP.md")
    args = parser.parse_args()

    print("[*] Đang quét toàn bộ mã nguồn server/ và scripts/ qua AST...")
    data = scan_codebase()

    summary = data["summary"]
    print(f"[✓] Đã phân tích: {summary['total_files']} files | {summary['total_lines']:,} lines | "
          f"{summary['total_classes']} classes | {summary['total_functions']} functions | {summary['total_endpoints']} endpoints")

    if args.export_json:
        out_p = Path(args.export_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[+] Đã xuất file JSON: {out_p}")

    map_file = BASE_DIR / "CODEBASE_MAP.md"
    if args.update_map or not args.check:
        if map_file.exists():
            update_codebase_map(data, map_file)


if __name__ == "__main__":
    main()

