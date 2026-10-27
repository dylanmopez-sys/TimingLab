import os
import secrets
import statistics
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

SESSIONS = {}
SESSIONS_LOCK = threading.Lock()

BIT_ZERO_DELAY = 0.20
BIT_ONE_DELAY = 0.60
THRESHOLD_OFFSET = 0.40
MAX_BITS = 64


def cleanup_sessions():
    now = time.perf_counter()
    with SESSIONS_LOCK:
        expired = [token for token, session in SESSIONS.items()
                   if now - session["created_at"] > 900]
        for token in expired:
            SESSIONS.pop(token, None)


@app.get("/")
def inicio():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/styles.css")
def estilos():
    return send_from_directory(BASE_DIR, "styles.css")


@app.get("/app.js")
def javascript():
    return send_from_directory(BASE_DIR, "app.js")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/start")
def iniciar():
    cleanup_sessions()
    data = request.get_json(silent=True) or {}
    bit_count = data.get("bit_count")

    if not isinstance(bit_count, int) or bit_count < 8 or bit_count > MAX_BITS or bit_count % 8 != 0:
        return jsonify({"error": f"El mensaje debe ocupar entre 1 y {MAX_BITS // 8} bytes UTF-8."}), 422

    token = secrets.token_urlsafe(18)
    with SESSIONS_LOCK:
        SESSIONS[token] = {
            "created_at": time.perf_counter(),
            "last_time": None,
            "calibration_intervals": [],
            "calibration_count": 0,
            "bit_intervals": [],
            "expected_bit_count": bit_count,
        }

    return jsonify({"token": token})


@app.post("/api/event")
def evento():
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    event_type = data.get("type")

    if event_type not in ("calibration", "bit"):
        return jsonify({"error": "Tipo de evento no válido."}), 400

    with SESSIONS_LOCK:
        session = SESSIONS.get(token)
        if session is None:
            return jsonify({"error": "Sesión no encontrada o caducada. Iniciá otra transmisión."}), 404

        now = time.perf_counter()
        previous = session["last_time"]
        interval = None if previous is None else now - previous
        session["last_time"] = now

        if event_type == "calibration":
            session["calibration_count"] += 1
            if session["calibration_count"] > 1 and interval is not None:
                session["calibration_intervals"].append(interval)
            return jsonify({"ok": True})

        if len(session["bit_intervals"]) >= session["expected_bit_count"]:
            return jsonify({"error": "Ya se recibieron todos los bits de esta sesión."}), 409
        if interval is None:
            return jsonify({"error": "Falta calibración temporal."}), 409

        session["bit_intervals"].append(interval)

    return jsonify({"ok": True})


@app.post("/api/finish")
def finalizar():
    data = request.get_json(silent=True) or {}
    token = data.get("token")

    with SESSIONS_LOCK:
        session = SESSIONS.pop(token, None)

    if session is None:
        return jsonify({"error": "Sesión no encontrada o caducada."}), 404

    intervals = session["bit_intervals"]
    expected_count = session["expected_bit_count"]
    calibration = session["calibration_intervals"]

    if len(intervals) != expected_count:
        return jsonify({"error": f"Transmisión incompleta: se recibieron {len(intervals)} de {expected_count} bits."}), 422
    if not calibration:
        return jsonify({"error": "No se pudo calibrar el canal. Intentá de nuevo."}), 422

    baseline = statistics.median(calibration)
    threshold = baseline + THRESHOLD_OFFSET
    decoded_bits = ["1" if interval >= threshold else "0" for interval in intervals]
    decoded_bytes = bytes(int("".join(decoded_bits[i:i + 8]), 2)
                          for i in range(0, len(decoded_bits), 8))
    recovered = decoded_bytes.decode("utf-8", errors="replace")

    return jsonify({
        "recovered_message": recovered,
        "decoded_bits": "".join(decoded_bits),
        "intervals": [round(value, 4) for value in intervals],
        "calibration_baseline": round(baseline, 4),
        "threshold": round(threshold, 4),
        "bit_count": len(decoded_bits),
        "duration_seconds": round(sum(intervals), 3),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=False)
