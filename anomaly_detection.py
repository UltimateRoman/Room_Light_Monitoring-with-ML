import conf, json, time, math, statistics
from boltiot import Sms, Bolt
def compute_bounds(history_data,frame_size,factor):
    if len(history_data) < frame_size:
        return None

    if len(history_data) > frame_size:
        del history_data[0:len(history_data)-frame_size]
    Mn = statistics.mean(history_data)
    Variance = 0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor*math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER)
history_data=[]

while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("Error occured while retrieving data: "+data['value'])
        time.sleep(10)
        continue

    print ("Value: "+data['value'])
    sensor_value = 0
    try:
        sensor_value = int(data['value'])
    except e:
        print("Error occured while parsing the response: ",e)
        continue

    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
    if not bound:
        required_dc = conf.FRAME_SIZE-len(history_data)
        print("Not enough data to compute the Z-score, need ",required_dc," more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue

    try:
        if sensor_value > bound[0] :
            print ("The light intensity has increased abruptly. Sending an SMS....")
            response = sms.send_sms("Someone has turned on the lights.")
            print("Response: ",response)
        elif sensor_value < bound[1]:
            print ("The light intensity has decreased abruptly. Sending an SMS....")
            response = sms.send_sms("Someone has turned off the lights.")
            print("Response: ",response)
        history_data.append(sensor_value);
    except Exception as e:
        print ("Error: ",e)
    time.sleep(10)
