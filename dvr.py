#Name: Swathi Sariputi, Enrolment Number: BT19CSE098, Assignment-4

#Importing the neccesary libraries required
import sys
import time
import threading
from queue import Queue
import copy

# Function to update queue of each router after 2s
def update_queue(router,common,nodeinfo):
    for n in router['neighbor']:
        # acquiring queue lock so that 2 threads don't overwrite the data
        lck=common[n][1]
        temp={}
        lck.acquire()
        #Putting the dvr table in the neighbours of this thread
        for key, value in router['DVR'].items():
            temp[key] = value
        common[n][0].put((nodeinfo,copy.deepcopy(temp)))
        lck.release()
    queue = common[nodeinfo][0]
    # Loop untill all the neighbouring routers have sent the updated table
    while queue.qsize()!=len(router['neighbor']):
        continue
# Function to update the table using Bellman Ford equation
def bellman_ford(router,common,nodeinfo):
    queue = common[nodeinfo][0]
    newTable = copy.deepcopy(router['DVR'])
    # iterating over all the items of the queue
    while not queue.empty():
        nn,tables = queue.get()
        src = nodeinfo
        for dest,value in newTable.items():
            cost1 = value[0]
            cost2 = tables[dest][0]
            if cost2 != float('inf') and cost2 + newTable[nn][0] < cost1:
                newCost, newHop = cost2 + router['DVR'][nn][0], router['DVR'][nn][1]
                newTable[dest] = (newCost, newHop)
    changed = {}
    # updating the value and keeping track of all the links where a change occured
    for dest,value in newTable.items():
        if router['DVR'][dest][0]!=value[0] or router['DVR'][dest][1]!=value[1]:
            changed[dest]=value
        router['DVR'][dest] = value
    return changed
def task(router,common,id,node):
    # share table with neighbours and update table (neighbours.length > queue..size)
    i = 0;
    while i<4:
        i+=1
        update_queue(router,common,node)
        changed = bellman_ford(router,common,node)
        # print new table
        totalNodes = 0
        s=''
        s += "\tROUTER: {rname}\n".format(rname=node)
        s += "Destination\tCost\tNext Router\n"
        for dest,value in router['DVR'].items():
            if dest in changed.keys():
                s = s + ' *  '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
            else:
                s = s + '    '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
            totalNodes += 1
        s += '\n'
        # checking if all threads have appended the new table and printing
        common['lock'].acquire()
        common['finalString'][id] = s
        common['counter'].append(id)
        if(len(common['counter']) == totalNodes):
            print('----------------------------------ITERATION {iter}----------------------------------\n'.format(iter=i))
            for s in common['finalString']:
                print(s)
            common['finalString'] = [0]*totalNodes
            common['counter']=[]
        common['lock'].release()
        time.sleep(2)
        # loop the threads untill all have complete the current iteration
        while True:
            common['lock'].acquire()
            if id not in common['counter']:
                 common['lock'].release()
                 break
            common['lock'].release()
        while id in common['counter']:
            continue
# Function to print initial router information
def _print(router,nlist):
    s='----------------------------------INITIAL----------------------------------\n'
    for nodeinfo in nlist:
        s += "\tROUTER: {rname}\n".format(rname=nodeinfo)
        s += "Destination\tCost\tNext Router\n"
        for dest,value in router[nodeinfo]['DVR'].items():
            s = s + '    '+ dest + '\t\t' + str(value[0]) + '  \t   ' + value[1] + '\n'
        s += '\n'
    print(s)
# common dictionary having keys: {nodeinfo, counter, lock,finalString} for storing shared information.
# The key nodename contains the queue for each node where the updated tables are sent after each iteration amd also has a key lock.
common={}
# reading the file
file_name=sys.argv[1]
file = open(file_name,'r')
Lines = file.readlines()
count=0
node_count=0
nlist=''
# Router dictionary having keys as node names for storing router information.
# node name is a subsequent dictionary with keys: neighbor and DVR
router = {}
#taking router information from lines of file
for l in Lines:
    s=l.strip()
    if s=='EOF':
        break
    if count==0:
        node_count=int(s)
        count=1
    elif count==1:
        nlist=s.split(' ')
        for nodeinfo in nlist:
            common[nodeinfo]=[Queue(maxsize=node_count),threading.Lock()]
            router[nodeinfo]={}
            router[nodeinfo]['neighbor'] = []
            router[nodeinfo]['DVR'] = {}
            for n in nlist:
                router[nodeinfo]['DVR'][n]=(float('inf'),'NA')
            router[nodeinfo]['DVR'][nodeinfo]=(0,nodeinfo)
        count=2
    else:
        source,destination,cost=s.split()
        cost = float(cost)
        router[source]['DVR'][destination] = (cost,destination)
        router[destination]['DVR'][source] = (cost,source)
        router[source]['neighbor'].append(destination)
        router[destination]['neighbor'].append(source)
threads = []
common['counter']= []
common['lock'] = threading.Lock()
common['finalString'] = [0]*node_count
_print(router,nlist)
for id,node in enumerate(nlist):
    th = threading.Thread(target=task, args=(router[node],common,id,node))
    threads.append(th)
    th.start()
for th in threads:
    th.join()