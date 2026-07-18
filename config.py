import os

os.system("free -h | awk '/^Mem:/ { print $3  " '/' " $2}'")