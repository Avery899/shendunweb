import csv
import os
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)

# 简单内存存储，方便 GET 直接返回
squat_records = []
CSV_PATH = "server_squat_log.csv"


def load_from_csv():
    """启动时从 CSV 加载历史数据到内存"""
    global squat_records
    if not os.path.isfile(CSV_PATH):
        print("未找到历史数据文件，将从空数据开始")
        return

    try:
        with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            squat_records = list(reader)
            # 转换数值类型字段
            for record in squat_records:
                for key in ["count", "rep_min_knee_angle", "knee_angle", "hip_angle",
                           "best_depth_angle", "threshold_down", "threshold_up", "elapsed_seconds"]:
                    if key in record and record[key]:
                        try:
                            record[key] = float(record[key])
                        except (ValueError, TypeError):
                            pass
            print(f"成功加载 {len(squat_records)} 条历史记录")
    except Exception as e:
        print(f"加载历史数据失败: {e}")


def save_to_csv(data):
    """将收到的数据追加到服务器端 CSV，便于留档"""
    file_exists = os.path.isfile(CSV_PATH)
    try:
        with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(data.keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"写入服务器端 CSV 失败: {e}")


@app.after_request
def add_cors_headers(response):
    """允许本地文件 demo.html 直接跨域访问"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/squat", methods=["POST"])
def add_squat():
    """接收一次深蹲记录"""
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "invalid payload"}), 400
    
    # 补充缺失的时间戳
    data.setdefault("timestamp", datetime.now().isoformat(timespec="seconds"))
    squat_records.append(data)
    
    # 持久化到 CSV
    save_to_csv(data)
    
    return jsonify({"status": "ok"}), 201


@app.route("/api/squats", methods=["GET"])
def list_squats():
    """返回当前已存储的所有深蹲记录"""
    return jsonify(squat_records)


if __name__ == "__main__":
    # 启动时加载历史数据
    load_from_csv()
    # debug=True 方便本地开发
    app.run(host="0.0.0.0", port=5000)
