#/bin/bash

ssh -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -tt $( $(dirname "$0")/_get_ssh_params.sh ${1:-none} ) "${@:2}"
