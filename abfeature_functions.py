import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stat
from scipy import interpolate

def findabsorptionfeatures(wvl, flux, pix_range = 7, eta = 0.05, alpha = 0.01, minlinedepth=0):
    #Function that takes in a spectrum and tries to find all absorption features within that. The pix_range input variable
    #is what helps to potentially separate noise from absorption features.

    #Sort the spectrum
    srt = np.argsort(wvl)
    wvl = wvl[srt]
    flux = flux[srt]
    
    #Add zeros on both ends to prevent a common error from occurring
    flux = np.hstack((np.zeros(pix_range), flux, np.zeros(pix_range)))
    for m in range(pix_range):
        wvl = np.hstack((wvl[0] - (m+1)*(wvl[1]-wvl[0]), wvl, wvl[-1] + (m+1)*(wvl[-1]-wvl[-2])))
    
    #Find local minima
    minwvs = []
    minfluxs = []
    for i in np.arange(pix_range, len(wvl) - pix_range + 1):
        minimum = flux[i] < flux[i-1] and flux[i] < flux[i+1]
        if not minimum:
            continue
        for j in np.arange(pix_range+1):
            minimum = minimum and (wvl[i+j] not in minwvs) and (wvl[i-j] not in minwvs)
            if not minimum:
                break
        if not minimum:
            continue
        left = stat.linregress(wvl[i-pix_range: i], flux[i-pix_range: i])
        right = stat.linregress(wvl[i: i+pix_range], flux[i: i+pix_range])
        minimum = minimum and left.slope < 0 and left.pvalue < alpha and right.slope > 0 and right.pvalue < alpha
        if minimum:
            minwvs.append(wvl[i])
            minfluxs.append(flux[i])
            
    #Find the absorption feature bounds
    wvbounds = []
    maxfluxs = []
    for w in minwvs:
        i = int(np.where(wvl == w)[0])
        feature = True
        j = 0
        while feature:
            ml = stat.linregress(wvl[i-pix_range-j: i+1-j], flux[i-pix_range-j: i+1-j])
            if ml.slope > 0 or ml.pvalue > eta:
                if pix_range%2 == 0:
                    lowerbound = wvl[int(i-j-pix_range/2)]
                    mfl = flux[int(i-j-pix_range/2)]
                else:
                    lowerbound = wvl[int(i-j-pix_range/2 + 0.5)]
                    mfl = flux[int(i-j-pix_range/2 + 0.5)]
                feature = False
            j=j+1
        feature = True
        j = 0
        while feature:
            ml = stat.linregress(wvl[i+j: i+pix_range+j+1], flux[i+j: i+pix_range+j+1])
            if ml.slope < 0 or ml.pvalue > eta:
                if pix_range%2 == 0:
                    upperbound = wvl[int(i+j+pix_range/2)]
                    mfu = flux[int(i+j+pix_range/2)]
                else:
                    upperbound = wvl[int(i+j+pix_range/2 - 0.5)]
                    mfu = flux[int(i+j+pix_range/2 - 0.5)]
                feature = False
            j=j+1
        wvbounds.append((lowerbound, upperbound))
        maxfluxs.append(np.max([mfu, mfl]))

    #remove features that are below a minimum line depth
    keep=[]
    for i in range(len(wvbounds)):
        if maxfluxs[i]-minfluxs[i] >= minlinedepth:
            keep.append(i)
    return np.array(wvbounds)[keep], np.array(minwvs)[keep], np.array(minfluxs)[keep], np.array(maxfluxs)[keep]
