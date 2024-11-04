import serial
import time
import configparser
import serial.tools.list_ports

# 讀取 config.ini 檔案
config = configparser.ConfigParser()
config.read('config.ini')

# 讀取 config.ini 檔案中你的裝置的 VID 和 PID
target_vid = int(config.get('SerialConfig', 'target_vid'), 0)
target_pid = int(config.get('SerialConfig', 'target_pid'), 0)


def find_comport_by_vid_pid(vid, pid):
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.vid == vid and port.pid == pid:
            return port.device  # 回傳 COM Port 編號
    return None

com_port = find_comport_by_vid_pid(target_vid, target_pid)
# 從配置檔案中讀取 COM Port 和 Baud Rate
com_port = config.get('SerialConfig', 'com_port')
baud_rate = config.getint('SerialConfig', 'baud_rate')

# 定義連接函數
def connect_serial(baud_rate_arg = None):
    if baud_rate_arg is None:
        baud_rate_arg = baud_rate
    while True:
        try:
            # ser = serial.Serial(com_port, baud_rate, timeout=1)
            ser = serial.Serial(
                                port=com_port,
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

# 初始化連接
ser = connect_serial(19200)
ser.close()
ser = connect_serial()
start_time = 0
try:
    while True:
        try:
            # 如果有數據待接收
            if ser.in_waiting > 0:
                data1 = ser.readline()
                if b'Gas' in data1:
                    gasMeas = ser.readline().decode('utf-8').strip()  # 讀取並解碼字串
                    data = ser.readline().decode('utf-8').strip()  # 讀取並解碼字串
                    if 'Humidity' in data and 'Temperature' in data:
                        start2 = data.find(":")
                        end2 = data.find("%", start2)
                        start3 = data.find(":", end2)
                        end3 = data.find("*C", start3)

                        humidMeas = data[start2 + 1: end2].strip()
                        tempMeas = data[start3 + 1: end3].strip()

                        end_time = time.time()
                        if end_time - start_time >= 3.:
                            # print(end_time - start_time)
                            print("G" + '[' + gasMeas + ']%' + "  ", end='')
                            print("RH" + '[' + humidMeas + ']%' + "  ", end='')
                            print("T" + '[' + tempMeas + ']C', end='')
                            print()
                            start_time = time.time()



        except (serial.SerialException, OSError):
            # 連接中斷，嘗試重新連接
            print(f"{com_port} 連接中斷，正在重新連接...")
            ser.close()
            ser = connect_serial()  # 重新嘗試連接

except KeyboardInterrupt:
    print("中斷連接")

finally:
    ser.close()
    print(f"{com_port} 已關閉")
