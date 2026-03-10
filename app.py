from flask import Flask, render_template, jsonify, request
import subprocess
import platform
import socket
import datetime

app = Flask(__name__)

DEFAULT_HOSTS = [
    {"name": "Google DNS", "host": "8.8.8.8"},
    {"name": "Cloudflare DNS", "host": "1.1.1.1"},
    {"name": "Local Machine", "host": "127.0.0.1"},
    {"name": "Google", "host": "google.com"},
    {"name": "GitHub", "host": "github.com"},
]

def ping_host(host):
    try:
        is_windows = platform.system().lower() == "windows"

        if is_windows:
            command = ["ping", "-n", "1", "-w", "2000", host]
        else:
            command = ["ping", "-c", "1", "-W", "2", host]

        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        output = result.stdout

        if is_windows:
            # Windows success check
            if "TTL=" in output or "ttl=" in output:
                # Parse time from Windows output: "time=12ms" or "time<1ms"
                time_ms = None
                for line in output.split("\n"):
                    if "time" in line.lower() and ("ms" in line.lower()):
                        try:
                            if "time<" in line.lower():
                                time_ms = 1.0
                            elif "time=" in line.lower():
                                part = line.lower().split("time=")[1]
                                time_ms = float(part.split("ms")[0].strip())
                        except:
                            time_ms = None
                        break
                return {"status": "UP", "response_time": time_ms, "error": None}
            else:
                return {"status": "DOWN", "response_time": None, "error": "Host unreachable"}
        else:
            if result.returncode == 0:
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
    try:
        is_windows = platform.system().lower() == "windows"

        if is_windows:
            command = ["tracert", "-h", "15", "-w", "1000", host]
        else:
            command = ["traceroute", "-m", "15", host]

        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        output = result.stdout
        return output if output else "No output received"

    except subprocess.TimeoutExpired:
        return "Traceroute timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"


def resolve_dns(host):
    try:
        return socket.gethostbyname(host)
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