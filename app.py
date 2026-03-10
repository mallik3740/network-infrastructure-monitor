from flask import Flask, render_template, jsonify, request
import subprocess
import platform
import socket
import datetime

app = Flask(__name__)

# Default hosts to monitor
DEFAULT_HOSTS = [
    {"name": "Google DNS", "host": "8.8.8.8"},
    {"name": "Cloudflare DNS", "host": "1.1.1.1"},
    {"name": "Local Machine", "host": "127.0.0.1"},
    {"name": "Google", "host": "google.com"},
    {"name": "GitHub", "host": "github.com"},
]

def ping_host(host):
    """Ping a host and return status, response time"""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", "-W", "2", host]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            # Parse response time from output
            output = result.stdout
            time_ms = None
            for line in output.split("\n"):
                if "time=" in line:
                    try:
                        time_ms = float(line.split("time=")[1].split(" ")[0].replace("ms", ""))
                    except:
                        time_ms = None
                    break
            return {"status": "UP", "response_time": time_ms, "error": None}
        else:
            return {"status": "DOWN", "response_time": None, "error": "Host unreachable"}

    except subprocess.TimeoutExpired:
        return {"status": "DOWN", "response_time": None, "error": "Timeout"}
    except Exception as e:
        return {"status": "DOWN", "response_time": None, "error": str(e)}


def traceroute_host(host):
    """Run traceroute on a host"""
    try:
        param = "tracert" if platform.system().lower() == "windows" else "traceroute"
        command = [param, "-m", "10", host]
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
        return result.stdout if result.stdout else "No output received"
    except subprocess.TimeoutExpired:
        return "Traceroute timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def resolve_dns(host):
    """Resolve hostname to IP"""
    try:
        ip = socket.gethostbyname(host)
        return ip
    except:
        return "Unable to resolve"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/ping-all")
def ping_all():
    results = []
    for item in DEFAULT_HOSTS:
        ping_result = ping_host(item["host"])
        ip = resolve_dns(item["host"])
        results.append({
            "name": item["name"],
            "host": item["host"],
            "ip": ip,
            "status": ping_result["status"],
            "response_time": ping_result["response_time"],
            "error": ping_result["error"],
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        })
    return jsonify(results)


@app.route("/api/ping", methods=["POST"])
def ping_custom():
    data = request.json
    host = data.get("host", "")
    if not host:
        return jsonify({"error": "No host provided"}), 400

    ping_result = ping_host(host)
    ip = resolve_dns(host)
    return jsonify({
        "name": "Custom Host",
        "host": host,
        "ip": ip,
        "status": ping_result["status"],
        "response_time": ping_result["response_time"],
        "error": ping_result["error"],
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    })


@app.route("/api/traceroute", methods=["POST"])
def traceroute():
    data = request.json
    host = data.get("host", "")
    if not host:
        return jsonify({"error": "No host provided"}), 400
    result = traceroute_host(host)
    return jsonify({"host": host, "output": result})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)