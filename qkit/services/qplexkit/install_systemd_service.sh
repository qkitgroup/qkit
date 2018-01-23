#!/bin/bash
# -*- coding: utf-8 -*-
"""
simple script to start a service with user previleges using systemd
FIXME: to be tested ...
HR@KIT 2018
"""

sudo adduser qplexkit

sudo -u qplexkit mkdir ~qplexkit/.ssh
sudo cp ~/.ssh/authorized_keys ~qplexkit/.ssh/authorized_keys
sudo chown qplexkit:qplexkit ~/.ssh/authorized_keys

mkdir -p ~/.config/systemd/user/
echo "
[Unit]
AssertPathExists=/home/qplexkit/qplexkit

[Service]
WorkingDirectory=/home/qplexkit/qplexkit
ExecStart=/usr/bin/python /home/qplexkit/qplexkit/qkit/services/qplexkit/qplexkit.py
Restart=always
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=default.target
" > ~/.config/systemd/user/qplexkit.service

# allow to run systemd services a a user
sudo loginctl enable-linger qplexkit

#ssh qplexkit@server
systemctl --user enable qplexkit

