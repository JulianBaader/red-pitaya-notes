#! /bin/sh

apps_dir=/media/mmcblk0p1/apps

source $apps_dir/stop.sh

cat $apps_dir/mcpha/mcpha.bit > /dev/xdevcfg 
# add daq.bit with removed fir filter

$apps_dir/daq/daq-server &