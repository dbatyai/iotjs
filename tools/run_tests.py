#!/usr/bin/env python

import argparse
import json
import subprocess
import os

from common_py import path
from common_py.system.filesystem import FileSystem as fs
from common_py.system.platform import Platform

platform = Platform()


def report_skip(test, results):
    results["skip"] += 1
    reason = test.get("reason", "")
    print("\033[1;33mSKIP : %s    (reason: %s)\033[0m" % (test["name"], reason))


def report_pass(test, results):
    results["pass"] += 1
    print("\033[1;32mPASS : %s\033[0m" % (test["name"]))


def report_fail(test, results):
    results["fail"] += 1
    print("\033[1;31mFAIL : %s\033[0m" % (test["name"]))


def report_final(results):
    print("")
    print("\033[1;34mFinished with all tests\033[0m")
    print("\033[1;32mPASS : %d\033[0m" % (results["pass"]))
    print("\033[1;31mFAIL : %d\033[0m" % (results["fail"]))
    print("\033[1;33mSKIP : %d\033[0m" % (results["skip"]))


def check_expected(test, output):
    expected_file = test.get("expected")
    if expected_file:
        file_path = fs.join("expected", expected_file)
        try:
            with open(file_path) as input:
                if output != input.read():
                    return False
        except IOError:
            print("Expected file not found: %s" % (file_path))
            return False

    return True


def run_testset(testset, args, results):
    print("")
    print("\033[1;34mRunning: %s\033[0m" % (testset["path"]))

    iotjs = fs.abspath(args.iotjs)
    owd = fs.getcwd()
    fs.chdir(fs.join(path.TEST_ROOT, testset["path"]))

    for test in testset["tests"]:
        skip = test.get("skip", [])
        if "all" in skip or platform.os() in skip:
            report_skip(test, results)
            continue

        timeout = test.get("timeout", args.timeout)
        proc = subprocess.Popen(["timeout", "-k", "30", "%d" % (timeout * 60), iotjs, test["name"]], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = proc.communicate()[0]

        should_fail = test.get("fail", False)
        if bool(proc.returncode) == bool(should_fail) and check_expected(test, output):
            report_pass(test, results)
        else:
            report_fail(test, results)

    fs.chdir(owd)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('iotjs', action='store', help='IoT.js binary to run tests with')
    parser.add_argument('--timeout', type=int, action='store', default=5, help='Timeout for the tests in minutes (default: %(default)s)')
    return parser.parse_args()


def run_tests():
    args = get_args()

    with open(fs.join(path.TEST_ROOT, 'tests.json')) as data_file:
        testsets = json.load(data_file)["testsets"]

    results = {"pass":0, "fail":0, "skip":0}
    for testset in testsets:
        run_testset(testset, args, results)

    report_final(results)


if __name__ == "__main__":
    run_tests()
