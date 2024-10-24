# Updating the Image:

Download the SD card image zip file according to https://pavel-demin.github.io/red-pitaya-notes/alpine/

Replace `SD/apps/index.html` with `repo/alpine/apps/index.html`

Create a `SD/apps/daq folder` and copy the contents of `repo/projects/daq/app` and `repo/projects/daq/server` into it.

Insert the SD Card into the RP and connect it via ethernet.

Power the RP and connect to it via SSH.

Make the SD card writable `rw`.

Install some packages:

`apk add gcc make`

`lbu commit -d`

Navigate to `SSH/apps/daq` and run the Makefile. `make`


Make the SD card read only `ro`.

# Acquiring data
Connect IN1 to OUT1.

Start the server via SSH `./start.sh` or the browser.

Navigate to `repo/projects/daq/client`.

To save one set of oscilloscope data to a npy file run 

`python daq.py <ip> save`

To process multiple sets of the oscilloscope data (a simple histogram of the maxima is created) run

`python daq.py <ip> process`

The set size and number of sets can be edited.

`python daq.py <ip> <mode> --set_size=<set_size> --sets=<number of sets>`

The saved array can be accessed by [event][channel][sample].

The array to be processed can be accessed by [channel][sample].

The function "testing_setup" can be edited to allow for different configurations.

# Visualisation
A simple example for visualisation is provided in the Jupyter Notebook.

# Some thoughts
There is a weird workaround "cut_off" as the last few samples are always read incorectly. Therefore more samples are requested and the last ones discarded.

Some more tests on the configuration are neccessary (spectrum, rise time, fall time, generator rate, trigger level).

The daq-server is fully compatible with the mcpha-client.

A FPGA Image without or with a disabled FIR Filter might be interesting as the processing will be done on the client side, raw data is better.

We are planning on using MimoCoRB https://github.com/GuenterQuast/mimoCoRB as a buffer manager to directly analyze the recorded data.

Different Modes can be implemented (i.e. setting a fixed acquisition time/number)




