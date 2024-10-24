import socket
import struct
import numpy as np

import time


COMMANDS = {
    0: "reset histogram",
    1: "reset timer",
    2: "reset oscilloscope", 
    3: "reset generator",
    4: "set sample rate",
    5: "set negator mode (0 for disabled, 1 for enabled)",
    6: "set pha delay",
    7: "set pha threshold min",
    8: "set pha threshold max",
    9: "set timer",
    10: "set timer mode (0 for stop, 1 for running)",
    11: "read status", 
    12: "read histogram",
    13: "set trigger source (0 for channel 1, 1 for channel 2)", 
    14: "set trigger slope (0 for rising, 1 for falling)",
    15: "set trigger mode (0 for normal, 1 for auto)",
    16: "set trigger level",
    17: "set number of samples before trigger",
    18: "set total number of samples",
    19: "start oscilloscope",
    20: "read oscilloscope data",
    21: "set fall time",
    22: "set rise time",
    23: "set lower limit",
    24: "set upper limit",
    25: "set rate",
    26: "set probability distribution",
    27: "reset spectrum",
    28: "set spectrum bin",
    29: "start generator",
    30: "stop generator",
    31: "start daq"
}

SAMPLE_RATES = [1, 4, 8, 16, 32, 54, 128, 256]
INPUTS = {"IN1": 0, "IN2": 1}
TRIGGER_SLOPES = {"rising": 0, "falling": 1}
TRIGGER_MODES = {"normal": 0, "auto": 1}
MAXIMUM_SAMPLES = 8388607 #TODO not sure about this value
MIN_ADC_VALUE = -4096
MAX_ADC_VALUE = 4095
NUMBER_OF_GENERATOR_BINS = 4096
DISTRIBUTIONS = {"uniform": 0, "poisson": 1}
ACQUISITION_MODES = ['save', 'process']

PORT = 1001

PLOT_SPECTRUM = True

CUT_OFF = 100
"""
For some reason the last few samples are not read correctly.
Requesting 100 samples more and discarding them works.
This is a temporary fix.
"""

class rpControll:
    def __init__(self):
        self.sample_rate = None
        self.negators = {"IN1": None, "IN2": None}
        self.trigger_source = None
        self.trigger_slope = None
        self.trigger_mode = None
        self.trigger_level = None
        self.number_of_samples_before_trigger = None
        self.total_number_of_samples = None
        
        self.fall_time = None
        self.rise_time = None
        self.generator_rate = None
        self.distribution = None
        self.spectrum = None
        
        self.events_per_loop = None
        
        self.requested_count = 0
    
    def connect(self, ip):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.socket.connect((ip, PORT))
        self.socket.settimeout(1)
        return True
    
    def command(self, code, number, value):
        #print("Sending command: ", COMMANDS[code], " with number ", number, " and value ", value)
        #print(COMMANDS[code])
        self.socket.sendall(struct.pack("<Q", code << 56 | number << 52 | (int(value) & 0xFFFFFFFFFFFFF)))
    
    
    # Set Configuration
    def set_sample_rate(self, rate):
        if rate not in SAMPLE_RATES:
            raise ValueError("Invalid sample rate")
        self.sample_rate = rate
        self.command(4, 0, rate)
        
    def set_negator(self, negated, channel):
        if negated:
            value = 1
        else:
            value = 0
        if channel not in INPUTS:
            raise ValueError("Invalid channel")
        self.negators[channel] = value
        self.command(5, INPUTS[channel], value)
        
    def set_trigger_source(self, channel):
        if channel not in INPUTS:
            raise ValueError("Invalid channel")
        self.trigger_source = channel
        self.command(13, INPUTS[channel], 0)
        
    def set_trigger_slope(self, slope):
        if slope not in TRIGGER_SLOPES:
            raise ValueError("Invalid slope")
        self.trigger_slope = slope
        self.command(14, 0, TRIGGER_SLOPES[slope])
        
    def set_trigger_mode(self, mode):
        if mode not in TRIGGER_MODES:
            raise ValueError("Invalid mode")
        self.trigger_mode = mode
        self.command(15, 0, TRIGGER_MODES[mode])
        
    def set_trigger_level(self, level):
        if not isinstance(level, int):
            raise ValueError("Invalid level (must be integer)")
        if level < MIN_ADC_VALUE or level > MAX_ADC_VALUE: #TODO does a negative level make sense?
            raise ValueError("Invalid level (out of range)")
        self.trigger_level = level
        self.command(16, 0, level)
        
    def set_number_of_samples_before_trigger(self, number):
        if not isinstance(number, int):
            raise ValueError("Invalid number (must be integer)")
        if number < 0 or number > MAXIMUM_SAMPLES:
            raise ValueError("Invalid number (out of range)")
        if self.total_number_of_samples is not None and number > self.total_number_of_samples:
            raise ValueError("Invalid number (must be less than total number of samples)")
        self.number_of_samples_before_trigger = number
        self.command(17, 0, number)
        
    def set_total_number_of_samples(self, number):
        if not isinstance(number, int):
            raise ValueError("Invalid number (must be integer)")
        if number < 0 or number > MAXIMUM_SAMPLES:
            raise ValueError("Invalid number (out of range)")
        if self.number_of_samples_before_trigger is not None and number < self.number_of_samples_before_trigger:
            raise ValueError("Invalid number (must be greater than number of samples before trigger)")

        self.osc_bytes = np.zeros(2 * number, dtype=np.int16).nbytes
        self.cut_bytes = np.zeros(2 * CUT_OFF, dtype=np.int16).nbytes
        
        self.cut_view = np.zeros(2 * CUT_OFF, dtype=np.int16).view(np.uint8)
        
        self.total_number_of_samples = number
        self.command(18, 0, number + CUT_OFF)
        
    def set_generator_fall_time(self, time):
        #TODO check if time is valid
        #TODO unit of time
        self.fall_time = time
        self.command(21, 0, time)
    
    def set_generator_rise_time(self, time):
        #TODO check if time is valid
        #TODO unit of time
        self.rise_time = time
        self.command(22, 0, time)
        
    def set_generator_rate(self, rate):
        #TODO check if rate is valid
        #TODO unit of rate
        self.generator_rate = rate
        self.command(25, 0, rate)
        
    def set_generator_distribution(self, distribution):
        if distribution not in DISTRIBUTIONS:
            raise ValueError("Invalid distribution")
        self.distribution = distribution
        self.command(26, 0, DISTRIBUTIONS[distribution])
        
        
    def set_generator_spectrum(self, spectrum):
        #TODO check if spectrum is valid
        if len(spectrum) != NUMBER_OF_GENERATOR_BINS:
            raise ValueError("Invalid spectrum")
        self.spectrum = spectrum
        for value in np.arange(NUMBER_OF_GENERATOR_BINS, dtype=np.uint64) << 32 | self.spectrum:
            self.command(28, 0, value)
            
        
        
    def reset_spectrum(self):
        self.command(27, 0, 0)
        
    def set_spectrum(self):
        raise NotImplementedError()
    
    def start_generator(self):
        self.command(29, 0, 0)
        
    def stop_generator(self):
        self.command(30, 0, 0)
        
    def reset_oscilloscope(self):
        self.command(2, 0, 0)
    
    def start_oscillocsope(self):
        self.command(19, 0, 0)
        
    def acquire_set(self, amount):
        buffer = np.zeros(amount*2*self.total_number_of_samples, dtype=np.int16)
        view = buffer.view(np.uint8)
        reshaped = buffer.reshape((2, self.total_number_of_samples, amount), order='F').transpose((2, 0, 1))
        self.command(31, 0, amount)
        
        for i in range(amount):
            bytes_received = 0
            while bytes_received < self.osc_bytes:
                bytes_received += self.socket.recv_into(view[i*self.osc_bytes+bytes_received:], 
                                                        self.osc_bytes - bytes_received)
            
            bytes_received = 0
            while bytes_received < self.cut_bytes:
                bytes_received += self.socket.recv_into(self.cut_view[bytes_received:],
                                                        self.cut_bytes - bytes_received)
            
        return reshaped
    
    def acquire_single(self, set_size):
        while True:
            buffer = np.zeros(2*self.total_number_of_samples, dtype=np.int16)
            view = buffer.view(np.uint8)
            reshaped = buffer.reshape((2, self.total_number_of_samples), order='F')
            self.command(31, 0, set_size)
            for i in range(set_size):
                bytes_received = 0
                while bytes_received < self.osc_bytes:
                    bytes_received += self.socket.recv_into(view[bytes_received:], 
                                                            self.osc_bytes - bytes_received)
                    
                bytes_received = 0
                while bytes_received < self.cut_bytes:
                    bytes_received += self.socket.recv_into(self.cut_view[bytes_received:],
                                                            self.cut_bytes - bytes_received)
            
                yield reshaped.copy()
            
        
    
    def testing_setup(self, ip):
        self.connect(ip)
        self.set_sample_rate(4)
        self.set_negator(0, "IN1")
        self.set_negator(0, "IN2")
        
        self.set_trigger_source("IN1")
        self.set_trigger_slope("rising")
        self.set_trigger_mode("normal")
        self.set_trigger_level(100)
        
        self.set_total_number_of_samples(1000)
        self.set_number_of_samples_before_trigger(100)
        
        self.set_generator_fall_time(10)
        self.set_generator_rise_time(100)
        self.set_generator_distribution("poisson")
        self.set_generator_rate(1000)
        
        
        self.set_generator_spectrum(np.load("generators/comb.npy"))
        self.start_generator()
        
        self.reset_oscilloscope()
        self.start_oscillocsope()
        

    


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Run the DAQ')
    # Required positional arguments
    parser.add_argument('ip', type=str, help='IP address of the Red Pitaya')
    parser.add_argument('mode', type=str, help='Acquisition mode', choices=ACQUISITION_MODES)

    # Optional arguments
    parser.add_argument('--set_size', type=int, help='Size of one dataset to be acquired', default=1000)
    parser.add_argument('--sets', type=int, help='Amount of sets to acquire if mode is "process"', default=10)
    args = parser.parse_args()
    
    print(f"Connecting to Red Pitaya at {args.ip}")
    
    rp = rpControll()
    rp.testing_setup(args.ip)
    
    if args.mode == 'save':
        print("Starting acquisition")
        start_time = time.time()
        np.save("data.npy", rp.acquire_set(args.set_size))
        stop_time = time.time()
        
        print(f"Acquired {args.set_size} events at an average rate of {args.set_size/(stop_time-start_time)} Hz")
        
    elif args.mode == 'process':
        print("Starting processing")
        import matplotlib.pyplot as plt
        
        hist=np.zeros(2**13)
        total_sets = args.set_size*args.sets
        
        generator = rp.acquire_single(1000)
        
        start_time = time.time()
        for i in range(total_sets):
            hist[np.max(next(generator)[0])]+=1
        np.save("hist.npy", hist)
        stop_time = time.time()
        print(f"Acquired {total_sets} events at an average rate of {total_sets/(stop_time-start_time)} Hz")
        
        plt.plot(hist)
        plt.show()
        