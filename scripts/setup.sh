#!/bin/bash
#check if we have an argument to config the bucket name
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -b|--bucket)
            bucket_name="$2"
            ;;
        -h|--help)
        echo "Usage:"; 
        echo "${0} --bucket \"<your S3 bucket name here>\" "
        exit 0
            ;;
    esac
    shift
done

[[ ${bucket_name} ]] || exit 1

sudo apt-get update
sudo apt install python3-pip -y

#install python dependencies
cd ..
pip3 install -r ./requirements.txt &&

current_folder=$(pwd)

#replace the bucket name in the service config files
sed -i "s|tbd|${bucket_name}|" ${current_folder}/service_files/nagios-nest.config

#replace working dir in service file
sed -i "s|dir1|${current_folder}|" ${current_folder}/service_files/nagios-nest.service

#replace config location in service file
sed -i "s|dir2|${current_folder}|" ${current_folder}/service_files/nagios-nest.service

#place the service file in it's target folder
sudo cp ${current_folder}/service_files/nagios-nest.service /etc/systemd/system/

#reload the demon and start the service
sudo systemctl daemon-reload
sudo systemctl start nagios-nest.service
sudo systemctl enable nagios-nest.service