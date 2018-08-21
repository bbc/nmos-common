#!/bin/bash

cd nmos-joint-ri/vagrant
export NMOS_RI_COMMON_BRANCH=$BRANCH_NAME
vagrant up --provision