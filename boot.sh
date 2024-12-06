#!/bin/bash
source venv/bin/activate
set -m
./main_process &
./proxy_process
fg %1