"""교육 안내 발송 자동화.

지금은 안내서(별첨2) PDF 생성만 들어 있다. 메일·문자 발송은 뒤이어 붙인다.
"""

from edu_notify.pdf import Notice, build, read_rows

__all__ = ["Notice", "build", "read_rows"]
