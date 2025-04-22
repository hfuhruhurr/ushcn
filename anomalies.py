## Source: https://drive.google.com/file/d/1-7mPgtU5fqQDQdCNjArVxEaT4XEMSU7e/view
##
## Disclaimer:  As much as I'd like to take credit for writing this script
##              I can't, because I didn't ;) -- I did tweak it in a couple
##              of places, though.  I also added a bunch of comments in an
##              attempt to explain what goes on in this script.
##
##
## Here's how to get the data and run the code
##
## (First, if you don't have python installed on your system,
##  go to www.python.org and install it.)
##
## 1) Download GHCN V3 data from ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/v3/
##
## Dude: there is Version 4 now.
##       Version 3's most recent data file timestamp is 2019-08-21.
##
##    The file ghcnm.tavg.latest.qca.tar.gz contains "homogenized" temperature data
##    The file ghcnm.tavg.latest.qcu.tar.gz contains raw temperature data.
##
##
## 2) Grab this file from the NASA/GISS web-site.
##
##     http://data.giss.nasa.gov/gistemp/graphs_v3/Fig.A.txt
##
##     This file contains the official results that NASA has computed
##     from the GHCN V3 data.  The second column in the file contains
##     the annual-average results.  These are the results you will want
##     to use as a baseline to compare your own results with.
##    
##
## 3) Unpack the files to extract the temperature data and metadata files 
##  
##   Unix/Linux: tar zxvf ghcnm.tavg.latest.qca.tar.gz
##               tar zxvf ghcnm.tavg.latest.gcu.tar.gz
##
##   Windows/Mac -- use your file-manager to launch the appropriate
##                  file unpacking utility.
##
##   A folder with a name of the form "ghcnm.v3.1.0.YYYYMMDD will be
##   created -- YYYYMMDD is the date that the data snapshot was released.
##
##   Inside that folder, you will find two files with the following filename format:
##
##                      ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.inv
##                      ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.dat
##
##    The YYYYMMDD part represents the release date of the particular data file.
##
##    Note: qcu.inv and qcu.dat files correspond to raw temperature data.
##          qca.inv and qca.dat files correspond to homogenized/adjusted temperature data.
##
##    The .dat files contain the actual temperature data.
##    The .inv files contain "metadata" (station latitude/longitudes, rural/urban
##    status, etc).
##
##
## 4) To run the python script with no command-line arguments, you will first
##    need to copy the temperature data and metadata files to the folder
##    containing this python script.
##
##    i.e. for raw data, use your file manager to copy the 
##
##                      ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.inv 
##                                  and
##                      ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.dat 
##
##    files to the folder containing this python script.
##
##    Then rename the "ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.inv" file to "v3.inv".
##    Rename the "ghcnm.tavg.v3.1.0.YYYYMMDD.qcu.dat" file to "v3.mean"
##
##    For adjusted/homogenized data, you will do the same, except that you
##    will be replacing "qcu" with "qca" in the above filenames.
##
##
## 5) If you rename the file ghchm.tavg.v3.1.0.YYYYMMDD.qcu.inv to v3.inv and
##    rename the file ghcnm.tavg.v3.1.0.YYYYMMDD.gcu.dat to v3.mean per step 4 
##    above, you can run the script by doing the following: 
##
##         Open a terminal window -- i.e. for Windows, open a DOS command window.
##         Then cd to the folder where you have this python script and 
##         data/metadata files, and run the following command.
##
##         python ghcn-simple.py
##
##         Remember that this python script (ghcn-simple.py) and the 
##         v3.inv/v3.mean files *must* be in the same folder.
##
##    The script will crunch on the data for a minute or two, depending on
##    how fast your computer is. Maybe less time, if you have a powerful
##    pc/laptop.
##    
##    The results will be dumped out to the terminal screen.
##
##    To put the results into a file that you can plot, do this:
##
##    python ghcn-simple.py > results.csv
##
##    The results will be saved in CSV (comma-separated values) format for easy 
##    plotting with Excel or OpenOffice.
##
##    The program crunches all (rural+suburban+urban) data together by default.
##
##
## 6) You can "customize" your runs a bit with command-line arguments.
##
##    To crunch just rural data, do this:
##
##    python ghcn-simple.py v3.inv v3.mean R > rural.csv
##
##
##    To crunch just urban data, do this:
##
##    python ghcn-simple.py v3.inv v3.mean U > urban.csv
##
##
##    To crunch just suburban data, do this:
##
##    python ghcn-simple.py v3.inv v3.mean S > suburban.csv
##
##
## 7) Try separate runs for different combos: raw, adjusted, raw and adjusted rural, 
##    raw and adjusted urban data.
##
##    Plot up your results and compare with the official NASA results that you
##    downloaded in step(2).
##
##

import sys, math

# constants
years  = range(1880,2011)
months = range(1,13)

# grid sampling in degrees
# The grid size is set to 20x20 degrees
# so we don't have to worry about interpolating
# to empty grid cells.
# The standard grid-cell size of 5x5 leaves enough
# empty grid cells in the Southern Hemisphere that the
# Northern Hemisphere gets overweighted in the average.
# This causes the results to show too much warming.
# Increasing the grid-cell size to 20x20 alleviates the 
# "empty grid-cell" problem enough to produce results
# much more in line with the NASA/GISS "meteorological
# stations" index.
grid   = 20  


# optional command line arguments: inventory-file data-file population-code
fileinv = "v3.inv" if len(sys.argv) <= 1 else sys.argv[1]
filedat = "v3.mean" if len(sys.argv) <= 2 else sys.argv[2]
popcls  = "RSU"     if len(sys.argv) <= 3 else sys.argv[3]

# station data, indexed by station id
station_locn = {}  # latitude, longitude stored by station id
station_data = {}  # temperature data stored by station id, year, month

print >> sys.stderr, " "
print >> sys.stderr, "Grid size: ",grid,"x",grid," degrees..."
print >> sys.stderr, " "

# Read and store the station metadata -- this has the station ID#'s,
# the station locations (latitude/longitude), and the station type
# (rural, suburban, or urban).
for line in open(fileinv):
  id = line[0:11]
  if line[73] in popcls:  # check rural/suburban/urban
    station_locn[id] = ( float(line[12:20]), float(line[21:30]) )  # location
    station_data[id] = {}  # initialise temperature data


print >> sys.stderr, "Just read in the station metadata..."
print >> sys.stderr, " "
print >> sys.stderr, "Now read in the station data (could take some time)..."
print >> sys.stderr, " "


# Read and store the actual temperature data.
# The temperature data will be indexed by station ID#, year, and month.
#
# Example:    station_data[47566][1954][3] will contain the March 1954 
# monthly average temperature for station# 47566.
# (Note: I just made up the station# for illustrative purposes).
#
for line in open(filedat):
  id = line[0:11]                                 # get station id
  if id in station_data:
    year = int( line[11:15] )                     # get year
    station_data[id][year] = {}
    for month in months:
      temp = int( line[11+8*month:16+8*month] )
      flag = line[16+8*month:19+8*month]
      if temp != -9999 and flag[0:2] == "  ":     # check for error flags
        station_data[id][year][month] = 0.01*temp  # if ok, store data


print >> sys.stderr, "Just read in the temperature data..."
print >> sys.stderr, "#Stations and #station locations below..."
print >> sys.stderr, len(station_locn), len(station_data)
print >> sys.stderr, " "

# Now calculate monthly baselines for each station.
# These baseline values will be used to convert the temperature readings 
# into anomalies.
#
# Without this step, missing months will add warming or cooling noise
# depending on the season, and the introduction of new stations will
# add warming or cooling noise depending on whether the new stations
# are in hotter of colder regions.

# We will compute 1951-1980 baseline average temperatures for all stations.
# A separate baseline average 1951-1980 temperature will be calculated for
# each month.  That is, for station#, say 47566, we will calculate
# the average 1951-1980 January temperature, the average 1951-1980 
# February temperature, etc.  If the station has enough valid data
# for the 1951-1980 period for all months, there will be 12 baseline
# average temperature values for that station (1 per month).
#
# We will have a big array of baseline average temperatures indexed
# by station id and month. The array is called "baselines"
# I.e. baselines[47566][1] will contain the average 1951-1980
# January temperature for station# 47566.  baselines[56678][6]
# will contain the average 1951-1980 June temperature for station
# number 56678 (once again, a made-up number).
#
#
# Remember that not all stations have enough data to compute
# valid 1951-1980 baseline temperatures. Some stations may
# not have any data for that period.  Those stations will
# be completely excluded from the processing. 
# If a station has at least 15 valid temperature samples for
# any month for the 1951-1980 baseline period, a baseline
# temperature will be calculated for that station and month.
#
# If a station does not have at least 15 samples for a given
# month, that station/month will be excluded from the calculations.
# If that station has enough samples (15 or more) for other months
# during the 1951-1980 baseline period, those months *will* be
# included in the calculations.
#
# Thus, not all stations in the GHCN data-set will be included
# in the calculations. Even so, there are thousands of stations
# that will still be used (way more than enough to compute good
# global-average temperature estimates, BTW).
#
# The python nested "dictionary" capability makes it easy to "skip over"
# missing months/years for any station without too many coding headaches.  

print >> sys.stderr, "Now start crunching the baselines..."
print >> sys.stderr, " "

baselines = {}
baselineCount=0
baselineValid=0
for id in station_data:
  # calculate mean temp by month over the years 1951-1980
  mtemps = {}
  for month in months:
    mtemps[month] = []
  for year in station_data[id]:
    if year >= 1951 and year <= 1980:
      for month in station_data[id][year]:
        mtemps[month].append( station_data[id][year][month] )

  # Calculate averages, but only include data if we have a robust baseline 
  # for this station id/month
  #
  # A station must have a minimum of 15 valid temperature values in
  # the time period 1951-1980 for a baseline to computed for that
  # station and month.
  #
  # For example, if station XXXXXX has only 12 valid average temperatures
  # for the month of March during the time period 1951-1980, no March baseline
  # will be computed for that station.  That station will then be excluded from
  # any temperature calculations for the month of March.  If valid baselines
  # for station XXXXXX can be computed for other months, station XXXXXX will
  # be included in the global-average anomaly calculations for those months.        
  baselines[id] = {}
  baselineValid=0
  for month in months:
    if len(mtemps[month]) >= 15:
      baselines[id][month] = sum( mtemps[month] ) / len( mtemps[month] )
      baselineValid=1
  if baselineValid:
    baselineCount+=1

print >> sys.stderr, "Just finished calculating baselines..."
print >> sys.stderr, "#stations with valid baseline data = ", baselineCount
print >> sys.stderr, " "
print >> sys.stderr, "Now start crunching the anomalies (could take some time)..."
print >> sys.stderr, " "

# Below, we will calculate average anomalies by assigning stations to 
# latitude/longitude grid-cells, averaging the station data in each grid-cell
# to produce year/month anomalies for that grid-cell, and then averaging over
# all grid-cells to produce global-average year/month anomalies.
#
# For all stations with valid baseline data, we will subtract the stations' 
# the 1951-1980 monthly baseline temperatures from the stations' raw temperatures
# for each month. We will do this separately for each month and year.
#
# That is, for station 47566, we will subtract station 47566's January
# 1951-1980 baseline temperature from *all* January temperatures for that station.
# We will then subtract that station's February 1951-1980 baseline average
# temperature from *all* of that station's February temperatures. We will
# do this for all months and all stations.  These are known as temperature
# "anomalies" (aka a $10 word for "changes").
#
# The result is that when we average everything together (see below), we will 
# not be averaging absolute temperatures, but temperature *changes* aka
# *anomalies* relative to the 1951-1980 baseline period. 
#
# Now, for each year, we could simply average together the anomalies for 
# all stations to get a single global average anomaly estimate for 
# each month of that year.  That is, don't bother with gridding (described
# in more detail below) and simply average the station data directly. If you 
# do that, you will get crude global temperature anomaly estimates that 
# are not too far "out of the ballpark".  
#
# Unfortunately, this approach has a big problem.  It assumes that all 
# the stations are evenly distributed around the globe.  But it turns out 
# that stations are "concentrated" in certain areas like the continental 
# USA and Western Europe. A simple direct station average would mean that 
# temperature data from those areas would get too much weighting relative 
# to temperatures in the rest of the world, where the temperature station 
# network is much more sparse.
#
# A way to work around this problem is to divide up the world into
# grid squares. For the purposes of this explanation, we will simply
# assume that the grid-square areas are identical. (In reality, they
# aren't, and we compensate for that).  But for this hypothetical
# explanation, we will assume that they are.
#
# Given that the stations are not distributed evenly, some grid squares
# will have lots of stations, while others may have just one or a few.
# To keep areas with lots of stations from being overweighted in the
# average, we will, for each grid square, compute a single average temperature 
# anomaly from all the temperature stations in that grid square.  Then we 
# will just average all the grid-square temperature anomalies together to get
# a single global-average anomaly for each month/year.
#
# In summary: Average together all stations in each grid cell. 
#             Each grid-cell will be represented by a *single* temperature
#             anomaly value (instead of, say 100, if we had 100 stations
#             in that particular grid-cell).  Data from all stations 
#             just gets "mashed together" in that grid-cell.
#
#             Then just average the grid-cell temperature average anomalies 
#             together to get the global average.  We do this for each
#             year/month
#
#             The end result is a single global-average temperature anomaly
#             for each year and month.
#
# By using a grid-square approach, that means that a grid-area in the
# USA that contains, say 100 stations, would not be weighted more in the
# global average than a equal-sized grid-square in Greenland that contains, 
# say, 3 stations.
#
# The method is not perfect, and there can be problems -- i.e. 
# if you have lots of empty grid squares, that will degrade the
# quality of your average results.  But for all of this method's shortcomings,
# it's still "good enough" to produce results that are very similar
# to the results you get from more sophisticated techniques.
#
# The big advantage here is that the grid-square method is very 
# simple -- easy to code up, and easy to explain -- but it still
# produces darned good global-average results that are very similar
# to much more difficult/sophisticated approaches.
#
# It's not perfect, but it's good enough.  And it is also relatively 
# easy to understand.

monthly = {}
for year in years:
  print>>sys.stderr, "Crunching temperature data for year", year
  monthly[year] = {}
  for month in months:
    # make a map of grid cells with a list of anomalies in each cell
    map = [[ [] for i in range(360/grid)] for j in range(180/grid)]
    # fill in all the anomalies for this month in the map
    for id in station_data:
      # store a list of all the station anomalies in every cell in the map
      if year in station_data[id]:
        if month in station_data[id][year]:
          # only include data if we have a baseline
          if month in baselines[id]:
            # anomaly = temperature - baseline
            anom = station_data[id][year][month] - baselines[id][month]
            # add the anomaly to the list for the given map cell
            # Compute a latitude and longitude index for each station.
            # These lat/long indices will be used to assign temperature
            # stations to lat/long grid-cells.
            lati = int((station_locn[id][0]+90.0)/grid)
            lngi = int((station_locn[id][1]+180.0)/grid)

            # Assign the temperature anomaly for this station
            # to the station's latidude/longitude grid-cell
            map[lati][lngi].append(anom)

    # Now loop over the grid cells
    # to compute the global-average anomalies.
    # The outputs of this averaging procedure are
    # global average anomalies for every year/month.
    stemp = 0.0
    swght = 0.0
    for lati in range(len(map)):
      w = math.cos(((lati+0.5)*grid-90.0)*3.1416/180.0)   # weight by cell area
      for lngi in range(len(map[lati])):
        if len( map[lati][lngi] ) > 0:
          t = sum( map[lati][lngi] ) / len( map[lati][lngi] )
          stemp += w*t
          swght += w
    stemp /= max( swght, 1.0e-20 )
    monthly[year][month] = stemp

## We now have anomalies for every year/month -- 
## Now average all monthly anomalies
## together for each year to produce a single average
## anomaly value for that year.  Dump into an easy-
## to-plot spreadsheet compatible format.
## The output will be global-average anomalies
## for all years beginning with 1880.
print "year",",","temp"
for year in years:
  yearavg=0
  for month in months:
    yearavg=yearavg+monthly[year][month]
  yearavg=yearavg/len(months)
  print year,",", yearavg


print >> sys.stderr, " "
print >> sys.stderr, "All finished!!"
print >> sys.stderr, " "