import configparser
import serial
import serial.tools.list_ports
import time
import asyncio
import websockets
import json

# server url
# uri = "ws://10.8.100.103:4000"  # Belle 伺服器 URI
# uri = "ws://192.168.123.101:4000"  # 機器狗 WebSocket 伺服器 URI
# uri = "ws://localhost:8765"  # 本機 WebSocket 伺服器 URI

# 讀取 config.ini 檔案
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


def find_comport_by_vid_pid():
    # 讀取 config.ini 檔案中你的裝置的 VID 和 PID
    target_vid = int(config.get('SerialConfig', 'target_vid'), 0)
    target_pid = int(config.get('SerialConfig', 'target_pid'), 0)
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == target_vid and port.pid == target_pid:
            return port.device  # 回傳 COM Port 編號
    return None


def find_baudrate():
    try:
        baud_rate = config.getint('SerialConfig', 'baud_rate')
    except:
        baud_rate = 9600
    return baud_rate


# 定義連接函數
def connect_serial(com_port, baud_rate_arg = None):
    if baud_rate_arg is None:
        baud_rate_arg = baud_rate
    while True:
        try:
            # ser = serial.Serial(com_port, baud_rate, timeout=1)
            ser = serial.Serial(port=com_port,
                                baudrate=baud_rate_arg,
                                bytesize=serial.EIGHTBITS,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                timeout=1  # 可調整為適合的值
                                )
            if ser.is_open:
                print(f"連接至 {com_port} 成功")
                return ser  # 成功連接後返回 ser 對象
        except serial.SerialException:
            print(f"無法連接至 {com_port}，正在重試...")
            time.sleep(1)  # 等待一秒後重試


# WebSocket 客戶端發送資料函數
async def send_data():
    uri = config.get('ServerConfig', 'server_uri')
    async with websockets.connect(uri) as websocket:
        print("成功連接至 WebSocket 伺服器")
        try:
            time_start0_end1 = [0, 0]
            while True:
                # 讀取 COM Port 資料
                gasMeas, humidMeas, tempMeas = capture_data_from_sensor(time_start0_end1)

                try:
                    interval_float = float(config.get('ServerConfig', 'interval'))
                except:
                    interval_float = 5.
                if time_start0_end1[1] - time_start0_end1[0] >= interval_float:
                    # 組裝 JSON 格式訊息
                    message = {
                        "gas": float(gasMeas),
                        "humidity": float(humidMeas),
                        "temperature": float(tempMeas)
                    }

                    # 將訊息轉為 JSON 格式並發送
                    await websocket.send(json.dumps(message))
                    print(f"已發送：{message}")
                    time_start0_end1[0] = time.time()

        except (serial.SerialException, OSError):
            print("連接中斷，正在重試...")


def capture_data_from_sensor(time_start0_end1):
    if ser.in_waiting > 0:
        data1 = ser.readline()
        if b'Gas' in data1:
            gasMeas = ser.readline().decode('utf-8').strip()
            data = ser.readline().decode('utf-8').strip()
            if 'Humidity' in data and 'Temperature' in data:
                start2 = data.find(":")
                end2 = data.find("%", start2)
                start3 = data.find(":", end2)
                end3 = data.find("*C", start3)

                humidMeas = data[start2 + 1: end2].strip()
                tempMeas = data[start3 + 1: end3].strip()

                time_start0_end1[1] = time.time()
                return gasMeas, humidMeas, tempMeas
    return 0, 0, 0



if __name__ == "__main__":
    com_port = find_comport_by_vid_pid()
    baud_rate = find_baudrate()

    ser = connect_serial(com_port, 19200)
    ser.close()
    ser = connect_serial(com_port)

    # 啟動 WebSocket 客戶端
    asyncio.run(send_data())
