import smbus
import time
import paho.mqtt.client as mqtt

# Define MQTT broker address, port, and topic
MQTT_BROKER_ADDRESS = "10.0.30.30"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "homeassistant/sensor/powerpi/state"

# MQTT credentials
MQTT_USERNAME = "homeassistant"
MQTT_PASSWORD = "password"

# Define I2C bus number
I2C_BUS = 1

# BH1750 address
BH1750_ADDR = 0x23

# Control commands
POWER_ON = 0x01
CONTINUOUS_LOW_RES_MODE = 0x13

# Initialize I2C bus
bus = smbus.SMBus(I2C_BUS)
time.sleep(1)

# Initialize MQTT client
mqtt_client = mqtt.Client(protocol=mqtt.MQTTv311)  # Specify MQTT version


# Function to read data from BH1750
def read_bh1750():
    data = bus.read_i2c_block_data(BH1750_ADDR, CONTINUOUS_LOW_RES_MODE, 2)
    return (data[1] + (256 * data[0])) / 1.2


# MQTT on_connect callback
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))


# Main function
def main():
    try:
        # Connect to MQTT broker
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        mqtt_client.on_connect = on_connect
        mqtt_client.connect(MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT)
        mqtt_client.loop_start()

        # Power on the sensor
        bus.write_byte(BH1750_ADDR, POWER_ON)

        # Initialize variables
        last_blink_time = time.time()
        blink_count = 0

        while True:
            brightness = read_bh1750()

            # Check for a brightness peak (blink)
            if brightness > 10:  # Adjust the threshold as needed
                # Calculate time since last blink
                current_time = time.time()
                time_since_last_blink = current_time - last_blink_time
                last_blink_time = current_time

                # Increment blink count
                blink_count += 1

                # Publish blink count to MQTT topic
                mqtt_client.publish(MQTT_TOPIC, str(blink_count))

                print("Blink detected! Count:", blink_count)
                print("Brightness:", brightness)

            # Add some delay to avoid high CPU usage
            time.sleep(
                0.03
            )  # Adjust the delay as needed for your desired sampling rate

    except KeyboardInterrupt:
        print("Measurement stopped.")
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
