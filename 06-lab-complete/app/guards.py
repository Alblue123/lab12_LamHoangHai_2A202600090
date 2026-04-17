import re

class InputGuardrails:
    def __init__(self):
        self.injection_patterns = [
            r"ignore (all )?(previous|above|prior) (instructions|directives|rules)",
            r"you are now",
            r"pretend (you are|to be)",
            r"act as (a |an )?(unrestricted|unfiltered|jailbroken)",
            r"disregard (all|any|your) (prior|previous|safety|instructions)",
            r"override (your |the )?(safety|system|instructions)",
            r"reveal (your |the )?(system ?prompt|instructions|config)",
            r"forget (your |all )?(instructions|rules|guidelines)",
            r"(show|tell|give)( me)? (the |your )?(admin |system )?(password|api.?key|secret|credential)",
            r"fill in.*(password|key|secret|connection|credential)",
            r"translate (your |all )?(instructions|system prompt|config)",
            r"output.*(json|yaml|xml|base64|rot13).*(config|prompt|instruction)",
            r"(bỏ qua|hãy tiết lộ|cho tôi xem|xuất toàn bộ).*(hướng dẫn|mật khẩu|api|thông tin)",
            r"what is the (admin |system )?(password|api.?key|database|connection)",
        ]
        self.allowed_topics = [
            "banking", "account", "transaction", "transfer", "loan",
            "interest", "savings", "credit", "deposit", "withdrawal",
            "balance", "payment", "atm", "card", "mortgage",
            # Romanized Vietnamese (no diacritics)
            "tai khoan", "giao dich", "tiet kiem", "lai suat",
            "chuyen tien", "the tin dung", "so du", "vay", "ngan hang",
            # Unicode Vietnamese (with diacritics)
            "tài khoản", "giao dịch", "tiết kiệm", "lãi suất", "lãi",
            "chuyển tiền", "thẻ tín dụng", "số dư", "vay", "ngân hàng",
            "thanh toán", "rút tiền", "nạp tiền", "thẻ atm", "tín dụng",
        ]
        self.blocked_topics = [
            "hack", "exploit", "weapon", "drug", "illegal",
            "violence", "gambling", "bomb", "kill", "steal",
        ]

    def _check_injection(self, user_input: str) -> dict:
        for pattern in self.injection_patterns:
            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                return {"safe": False, "matched_pattern": pattern, "matched_text": match.group()}
        return {"safe": True, "matched_pattern": None, "matched_text": None}

    def _check_topic(self, user_input: str) -> dict:
        text_lower = user_input.lower()
        for topic in self.blocked_topics:
            if topic in text_lower:
                return {"allowed": False, "reason": f"Blocked topic: '{topic}'"}
        for topic in self.allowed_topics:
            if topic in text_lower:
                return {"allowed": True, "reason": "On-topic"}
        return {"allowed": False, "reason": "Off-topic: no banking keywords found"}

    def check(self, text: str) -> tuple[bool, str]:
        if not text.strip():
            return False, "[BLOCKED by Input Guard] Empty input."
            
        injection_result = self._check_injection(text)
        if not injection_result["safe"]:
            matched = injection_result["matched_text"]
            return False, f"[BLOCKED by Input Guard] Malicious injection detected ('{matched}')"

        topic_result = self._check_topic(text)
        if not topic_result["allowed"]:
            reason = topic_result["reason"]
            return False, f"[BLOCKED by Input Guard] {reason}"
            
        return True, "Passed"

class OutputGuardrails:
    def __init__(self):
        self.pii_patterns = {
            "vn_phone":       r"0\d{9,10}",
            "email":          r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}",
            "cccd":           r"\b\d{9}\b|\b\d{12}\b",
            "api_key":        r"sk-[a-zA-Z0-9-]+",
            "password":       r"password\s*[:=]\s*\S+",
            "admin_password": r"admin123",
            "db_connection":  r"db\.[\w.-]+\.internal(:\d+)?",
            "secret_key":     r"secret[-_]?key\s*[:=]\s*\S+",
        }

    def check_and_redact(self, response: str) -> tuple[bool, str, str]:
        issues = []
        redacted = response
        for name, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                issues.append(f"{name} ({len(matches)})")
                redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)

        if len(issues) == 0:
            return True, response, "Passed"
        else:
            alert_msg = f"[MODIFIED by Output Guard] Redacted issues: {', '.join(issues)}"
            return True, redacted, alert_msg
