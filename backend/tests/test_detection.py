from app.detection import detect_event, summarize_events


def test_failed_login_creates_explainable_alert():
    alerts = detect_event({"event_type": "login_failed", "source_ip": "192.0.2.1", "details": ""})
    assert len(alerts) == 1
    assert alerts[0]["rule_id"] == "AUTH-001"
    assert alerts[0]["severity"] == "medium"
    assert alerts[0]["recommendation"]


def test_suspicious_path_is_detected():
    alerts = detect_event({"event_type": "web_request", "source_ip": "192.0.2.2", "details": "../private"})
    assert any(a["rule_id"] == "WEB-003" for a in alerts)


def test_normal_event_does_not_raise_alert():
    assert detect_event({"event_type": "normal_request", "source_ip": "192.0.2.3", "details": "ok"}) == []


def test_summary_counts_severity():
    result = summarize_events([{"severity": "high"}, {"severity": "info"}, {"severity": "high"}])
    assert result["total"] == 3
    assert result["high"] == 2
    assert result["info"] == 1
