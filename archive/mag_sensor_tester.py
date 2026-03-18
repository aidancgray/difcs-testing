from mag_read import MagSensor

DIFCS_IP = "172.16.2.61"
DIFCS_PORT = 8234
SER_MAG = 'COM6'


if __name__ == "__main__":
    mag = MagSensor(SER_MAG, 1)
    msg1 = mag.set_op(0,1)
    print(msg1)
    msg2 = mag.set_op(0,2)
    print(msg2)
    
    # count_data = mag.get_counts()
    # print(f'xs={count_data[0][0]}, xc={count_data[0][1]}')
    # print(f'ys={count_data[1][0]}, yc={count_data[1][1]}')

    # pos_data = mag.get_real_position()
    # print(f'xpos={pos_data[0]}, ypos={pos_data[1]}')
    
    # p = mag.get_PID(1, 'P')
    # print(f'P={p}')
