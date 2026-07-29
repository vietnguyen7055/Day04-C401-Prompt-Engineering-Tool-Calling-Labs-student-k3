"""Translate tool — Vietnamese ↔ English."""
from __future__ import annotations


VN_TO_EN = {
    "trí tuệ nhân tạo": "artificial intelligence",
    "học máy": "machine learning",
    "khoa học dữ liệu": "data science",
    "thị trường": "market",
    "tuyển dụng": "recruitment",
    "lương": "salary",
    "kỹ năng": "skills",
    "khóa học": "courses",
    "chứng chỉ": "certificate",
    "kinh nghiệm": "experience",
    "phần mềm": "software",
    "bảo mật": "security",
    "điện toán đám mây": "cloud computing",
    "robot": "robotics",
    "tự động hóa": "automation",
    "việc làm": "jobs",
    "công nghệ": "technology",
    "tin tức": "news",
    "hôm nay": "today",
}


def translate(text: str, target: str = "en") -> str:
    """Basic keyword translator for search optimization."""
    if target == "en":
        result = text
        for vn, en in VN_TO_EN.items():
            result = result.replace(vn, en)
        return result
    return text
