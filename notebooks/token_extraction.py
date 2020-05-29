import os
import pandas as pd
import re
import json
from const import NlpConst, varies, stoplist
import matplotlib.pyplot as plt

def f7(seq):
    """
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def find_ordering(dist):
    curr_sect = ''
    seq = []
    # for idx in range(0, len(dist['A'])):
    #     Tv = {key: dist[key][idx] for key in dist.keys()}
    #     # print(Tv)
    #     Keymax = max(Tv, key=Tv.get)
    #     if min(Tv, key=Tv.get) != max(Tv, key=Tv.get):
    #         curr_sect = Keymax
    #     # print(curr_sect)
    #     if curr_sect != '':
    #         seq.append(curr_sect)
    # ordering = f7(seq)
    # return ordering

    ### TODO: should only change curr_sect when consecutive changed
    for idx in range(0, len(dist['A']) - 2):
        Tv1 = {key: dist[key][idx+0] for key in dist.keys()}
        Tv2 = {key: dist[key][idx+1] for key in dist.keys()}
        #Tv3 = {key: dist[key][idx+2] for key in dist.keys()}
        # print(Tv)
        Keymax1 = max(Tv1, key=Tv1.get)
        Keymax2 = max(Tv2, key=Tv2.get)
        #Keymax3 = max(Tv3, key=Tv3.get)
        if min(Tv1, key=Tv1.get) != max(Tv1, key=Tv1.get):
            if min(Tv2, key=Tv2.get) != max(Tv2, key=Tv2.get):
                if Keymax1 == Keymax2:
                    curr_sect = Keymax1
        # print(curr_sect)
        if curr_sect != '':
            seq.append(curr_sect)
    ordering = f7(seq)
    return ordering

# split two parts
def split_in_two_at(dist, part_1, part_2):
    opt_split_at = 0
    total_sum = 0
    all_sums = []
    # find split_at such that part_1_sum + part_2_sum is MAX
    for split_at in range(0, len(dist['A'])):
        total_sum = sum(dist[part_1][0:split_at]) + sum(dist[part_2][split_at:])
        all_sums.append(total_sum)


    # Plot the MAX curve
    plt.plot(all_sums, label=f'{part_1} -> {part_2}')
    plt.ylabel('freq')
    plt.legend()
    plt.show()


    ### TODO: MAX may be multiple, should look forward choices.
    # Consider Full-Stop
    opt_split_at = all_sums.index(max(all_sums))
    inc = 0
    while opt_split_at+inc < len(all_sums) and all_sums[opt_split_at+inc] >= all_sums[opt_split_at]:
        inc = inc + 1
        print(str(inc))
    new_opt_split_at = opt_split_at + inc
    return new_opt_split_at

def split_points(dist, ordering):
    split_at = [0]
    for idx in range(len(ordering)-1):
        sp = split_in_two_at(dist, ordering[idx], ordering[idx+1])
        split_at.append(sp)
    split_at.append(len(dist['A'])-1)

    # print(split_at)
    return split_at