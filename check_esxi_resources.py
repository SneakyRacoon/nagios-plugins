#!/usr/bin/python
import sys
import pyVmomi
import argparse
import atexit
import itertools
from pyVim import connect
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect
import humanize

MBFACTOR = float(1 << 20)


def GetArgs():

    parser = argparse.ArgumentParser(
        description='Process args for retrieving all the Virtual Machines')
    parser.add_argument('-s', '--host', required=True, action='store',
                        help='Remote host to connect to')
    parser.add_argument('-o', '--port', type=int, default=443, action='store',
                        help='Port to connect on')
    parser.add_argument('-u', '--user', required=True, action='store',
                        help='User name to use when connecting to host')
    parser.add_argument('-p', '--password', required=False, action='store',
                        help='Password to use when connecting to host')
    args = parser.parse_args()
    return args


def main():
        args = GetArgs()

        si = connect.ConnectNoSSL(args.host, 443, args.user, args.password)
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()

        for datacenter in content.rootFolder.childEntity:
            datastores = datacenter.datastore
            hostFolder = datacenter.hostFolder
            computeResourceList = hostFolder.childEntity

        for computeResource in computeResourceList:
            hostList = computeResource.host

        host = hostList[0]
        datastore = datastores[0]

        summary = host.summary
        stats = summary.quickStats
        hardware = host.hardware

        #CPU
        cpuCapacityMhz = (host.hardware.cpuInfo.hz * host.hardware.cpuInfo.numCpuCores) / 1000 / 1000
        cpuUsageMhz = stats.overallCpuUsage
        cpuUsageMhzPercentage = int(100 * cpuUsageMhz / cpuCapacityMhz)

        #RAM
        memoryCapacity = hardware.memorySize
        memoryCapacityInMB = hardware.memorySize/MBFACTOR
        memoryUsage = stats.overallMemoryUsage
        freeMemoryPercentage = 100 - ((memoryUsage / memoryCapacityInMB) * 100)
        freeMemoryPercentageHumanized = int(round(freeMemoryPercentage, 0))

        #HDD
        dsSummary = datastore.summary
        capacity = dsSummary.capacity
        freeSpace = dsSummary.freeSpace
        uncommittedSpace = dsSummary.uncommitted
        freeSpacePercentage = (float(freeSpace) / capacity) * 100
        freeSpacePercentageHumanized = int(round(freeSpacePercentage, 0))

        #UpTime
        uptime = stats.uptime
        uptimeDays = int(uptime / 60 / 60 / 24)


        if cpuUsageMhzPercentage < 80 or freeMemoryPercentageHumanized > 20 or freeSpacePercentageHumanized > 20:
            print("OK - " + str(cpuUsageMhzPercentage) + "% CPU usage, " + str(freeMemoryPercentageHumanized) + "% Free Memory, " + str(freeSpacePercentageHumanized) + "% Free Disk space")
            sys.exit(0)
        elif cpuUsageMhzPercentage > 75 or freeMemoryPercentageHumanized < 25 or freeSpacePercentageHumanized < 25:
            print("Warning - " + str(cpuUsageMhzPercentage) + "% CPU usage, " + str(freeMemoryPercentageHumanized) + "% Free Memory, " + str(freeSpacePercentageHumanized) + "% Free Disk space")
            sys.exit(1)
        else:
            print("Critical - " + str(cpuUsageMhzPercentage) + "% CPU usage, " + str(freeMemoryPercentageHumanized) + "% Free Memory, " + str(freeSpacePercentageHumanized) + "% Free Disk space")
            sys.exit(2)




if __name__ == "__main__":
    main()
