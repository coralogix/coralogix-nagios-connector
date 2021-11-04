#!/bin/bash
#check if we have an argument to config the bucket name
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--bucket) bucket_name="$2"; 
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

[[ ${bucket_name} ]] || exit 1
 
sudo apt-get update
sudo apt install python3-pip -y
cd /home/ubuntu/ &&
cd nagios-alerts-connector
#replace the bucket name in the service config files
sed -i "s/tbd/${bucket_name}/" /home/ubuntu/coralogix-nagios-connector/nagios-nest.config

pip3 install -r ./requirements.txt
sudo cp /home/ubuntu/coralogix-nagios-connector/service_files/nagios-nest.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start nagios-nest.service
sudo systemctl enable nagios-nest.service