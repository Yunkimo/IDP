"""避免 query token 出现在 Uvicorn 握手与访问日志中。"""

import logging
import re


class QueryTokenFilter(logging.Filter):
    """移除日志 URL 的整个 query，兼容重复及编码后的参数名。"""

    def filter(self, record: logging.LogRecord) -> bool:
        """先完成日志插值，再脱敏，不保留原始参数。"""
        record.msg = re.sub(r"\?[^\s\"']*", "?[REDACTED]", record.getMessage())
        record.args = ()
        return True


def install_log_filters() -> None:
    """为应用使用的服务器日志添加幂等过滤器。"""
    for name in ("uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        if not any(isinstance(item, QueryTokenFilter) for item in logger.filters):
            logger.addFilter(QueryTokenFilter())
