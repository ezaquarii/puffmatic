#!/bin/sh

case $1 in
    "stdout")
	echo "stdout 1"
	echo "stdout 2"
	;;
    "stderr")
	echo "stderr 1" 1>&2
	echo "stderr 2" 1>&2
	;;    
    "stdout+stderr")
	echo "stdout 1"
	echo "stderr 1" 1>&2
	echo "stdout 2"
	echo "stderr 2" 1>&2
	;;
    "fail")
	echo "failing"
	exit 1
	;;
    *)
	echo "$0 stdout|stderr|stdout+stderr|fail"
	;;
esac
