"""
PhishGuard AI — Phishing URL Detection System
Main Flask Application Entrypoint & Controller
B.Tech CSE Industrial Training Capstone Project
"""

import os
import re
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
)
from config import config_by_name
from ml.train_model import load_or_train_model, analyze_url
from ml.feature_extractor import normalize_url
from database.models import (
    init_db,
    insert_scan,
    get_recent_scans,
    get_scan_by_id,
    get_stats,
    clear_history,
)

env_name = os.environ.get("FLASK_ENV", "default")
app_config = config_by_name.get(env_name, config_by_name["default"])

app = Flask(__name__)
app.config.from_object(app_config)

# Initialize database schema on startup
with app.app_context():
    init_db()


def validate_url_input(url_str: str):
    """
    Validate raw URL input string.
    Returns (is_valid, error_message, cleaned_url)
    """
    if not url_str or not url_str.strip():
        return False, "URL cannot be empty. Please enter a valid URL.", ""

    cleaned = url_str.strip()

    if len(cleaned) > 2048:
        return False, "URL exceeds maximum supported length (2048 characters).", ""

    # Basic structure check: must contain at least one dot or be an IP/localhost
    # Check for invalid control characters / whitespace inside
    if re.search(r"[\s<>\"'{}|\\^`]", cleaned):
        return False, "URL contains illegal whitespace or control characters.", ""

    normalized = normalize_url(cleaned)
    domain_match = re.search(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/?#]+)", normalized)
    if not domain_match or not domain_match.group(1):
        return False, "Malformed URL: Unable to resolve hostname/domain.", ""

    return True, "", cleaned


@app.route("/", methods=["GET"])
def index():
    """Home Dashboard: Input URL to scan, view live statistics & recent scans."""
    stats = get_stats()
    recent_scans = get_recent_scans(limit=5)
    return render_template("index.html", stats=stats, recent_scans=recent_scans)


@app.route("/scan", methods=["POST"])
def scan_url():
    """
    Scan URL endpoint: accepts both AJAX JSON and traditional HTML form submissions.
    """
    # Determine input from JSON or Form
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json
    if request.is_json:
        req_data = request.get_json(silent=True) or {}
        raw_url = req_data.get("url", "")
    else:
        raw_url = request.form.get("url", "")

    # Input validation
    is_valid, error_msg, cleaned_url = validate_url_input(raw_url)
    if not is_valid:
        if is_ajax:
            return jsonify({"success": False, "error": error_msg}), 400
        flash(error_msg, "danger")
        return redirect(url_for("index"))

    try:
        # Load model and analyze URL features
        model, _ = load_or_train_model()
        result = analyze_url(cleaned_url, model=model)

        # Record scan in SQLite database
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        scan_id = insert_scan(
            url=result["url"],
            prediction=result["status"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            features=result["features"],
            risk_flags_count=result["explanation"]["total_risk_flags"],
            client_ip=client_ip,
        )
        result["scan_id"] = scan_id

        if is_ajax:
            return jsonify({"success": True, "data": result})

        stats = get_stats()
        recent_scans = get_recent_scans(limit=5)
        return render_template(
            "index.html",
            scan_result=result,
            stats=stats,
            recent_scans=recent_scans,
            input_url=cleaned_url,
        )

    except Exception as e:
        app.logger.error("Scan processing error: %s", str(e))
        if is_ajax:
            return jsonify({"success": False, "error": f"Internal scan error: {str(e)}"}), 500
        flash("An error occurred while analyzing the URL. Please verify syntax and try again.", "danger")
        return redirect(url_for("index"))


@app.route("/history", methods=["GET"])
def history():
    """Scan History page: view past scan logs with search and status filtering."""
    search_query = request.args.get("q", "").strip()
    filter_status = request.args.get("filter", "All").strip()

    scans = get_recent_scans(
        limit=100,
        search_query=search_query if search_query else None,
        filter_status=filter_status if filter_status in ["Suspicious", "Likely legitimate"] else None,
    )
    stats = get_stats()

    return render_template(
        "history.html",
        scans=scans,
        stats=stats,
        search_query=search_query,
        filter_status=filter_status,
    )


@app.route("/history/clear", methods=["POST"])
def clear_scan_history():
    """Clear all records from scan history."""
    deleted_count = clear_history()
    flash(f"Successfully cleared {deleted_count} scan record(s) from SQLite database.", "info")
    return redirect(url_for("history"))


@app.route("/about", methods=["GET"])
def about():
    """About page: explain project architecture, feature engineering, and ethical disclaimer."""
    _, metrics = load_or_train_model()
    return render_template("about.html", metrics=metrics)


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """JSON API endpoint returning live system metrics."""
    stats = get_stats()
    return jsonify({"success": True, "stats": stats})


@app.route("/api/scan/<int:scan_id>", methods=["GET"])
def api_scan_detail(scan_id: int):
    """JSON API endpoint returning detailed feature breakdown for a specific scan."""
    scan = get_scan_by_id(scan_id)
    if not scan:
        return jsonify({"success": False, "error": "Scan record not found"}), 404
    return jsonify({"success": True, "scan": scan})


@app.errorhandler(404)
def not_found_error(error):
    """Custom 404 handler matching cybersecurity dark theme."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler matching cybersecurity dark theme."""
    return render_template("500.html"), 500


if __name__ == "__main__":
    # Pre-train or cache model on application startup
    print("=================================================================")
    print("  PhishGuard AI — Phishing URL Detection System")
    print("  B.Tech 3rd-Year CSE Industrial Training Project")
    print("  Server running at: http://127.0.0.1:5000")
    print("=================================================================")
    load_or_train_model()
    app.run(host="127.0.0.1", port=5000, debug=True)
