from licensePlate import ConfigurationData, LicensePlate
import creator as dsc
import time
def time_convert(sec):
    mins = sec // 60
    sec = sec % 60
    hours = mins // 60
    mins = mins % 60
    print("Time passed = {0}:{1}:{2}".format(int(hours),int(mins),sec))

configuration_file = "Configuration\Countries\TR\config.json"
config = ConfigurationData(configuration_file)
lpc = dsc.Creator([config.data],"D:\ArGe\Machine Learning\Datasets\Synthetic\LicensePlate\BaseImages", seperateTrainTestVal=False,destinationFolder="Dataset")
start_time = time.time()
lpc.create(10)
end_time  = time.time()
time_lapsed = end_time - start_time
time_convert(time_lapsed)