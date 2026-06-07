"""CSV 与 Excel 文件读取工具。"""

from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Union

import pandas as pd


FileInput = Union[str, Path, BinaryIO]


def _get_extension(file: FileInput) -> str:
    """从路径或 Streamlit 上传对象中获取扩展名。"""
    name = getattr(file, "name", file)
    return Path(str(name)).suffix.lower()


def _read_bytes(file: FileInput) -> bytes:
    """读取文件内容，并兼容路径和上传文件对象。"""
    if isinstance(file, (str, Path)):
        return Path(file).read_bytes()

    if hasattr(file, "seek"):
        file.seek(0)
    content = file.read()
    if hasattr(file, "seek"):
        file.seek(0)
    return content


def load_csv_or_excel(file: FileInput) -> pd.DataFrame:
    """读取 CSV 或 XLSX 文件并返回 DataFrame。

    CSV 依次尝试 UTF-8、UTF-8-SIG 和 GBK 编码；Excel 第一版支持 XLSX。
    """
    extension = _get_extension(file)
    content = _read_bytes(file)

    if extension == ".csv":
        errors = []
        for encoding in ("utf-8", "utf-8-sig", "gbk"):
            try:
                return pd.read_csv(BytesIO(content), encoding=encoding)
            except UnicodeDecodeError as error:
                errors.append(f"{encoding}: {error}")
        raise ValueError("CSV 编码识别失败，请将文件转换为 UTF-8 或 GBK。") from errors[-1]

    if extension == ".xlsx":
        return pd.read_excel(BytesIO(content), engine="openpyxl")

    raise ValueError("暂不支持该文件格式，请上传 .csv 或 .xlsx 文件。")
