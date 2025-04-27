### Goal

Originally, to replicate the charts used in [John Shewchuck's video](https://www.youtube.com/watch?v=cF16lDtSVrU).  The chart data comes from USHCN.

Subsequently, to replicate the chart in [his NEEM Project video](https://www.youtube.com/watch?v=folh5yyFyl8).  The chart data comes from EPICA (European Project for Ice Coring in Antartica).

### USHCN Data

Data is found at http://www.ncdc.noaa.gov/oa/climate/research/ushcn or ftp://ftp.ncdc.noaa.gov/pub/data/ushcn/v2.5.

4/19/2025:  The website url worked to download the files without issue.

4/26/2025:  The website continually errored out (503).  The ftp files worked though.

Files:
- readme.txt - explains files and their layouts
- status.txt - documents version changes (v2.5 current as of 4/26/2025)
- ushcn-v2.5-stations.txt - weather station information
- ushcd.\<element>.latest.\<dataset-type>.tar.gz (qty. 11) where:
  - \<element> = [prcp, tavg, tmax, tmin] where:
    - tmax = monthly mean maximum temperature
	- tmin = monthly mean minimum temperature
	- tavg = average monthly temperature (tmax+tmin)/2
 	- prcp = total monthly precipitation
  - \<dataset-type> = [raw, tob, FLs.52j] where:
    - raw = observed data value from the sensor
    - tob = Time of Observation Bias, adjusts for time of day of observation
    - FLs.52j = final, adjusted values using version 52j
  - Note: there is no tob file for prcp...hence, 11 files instead of 12.

### EPICA Dome C Ice Core Data

Two, corroborating sources:
1) Pangaea: https://doi.pangaea.de/10.1594/PANGAEA.683655?format=textfile
2) NOAA: https://www.ncei.noaa.gov/pub/data/paleo/icecore/antarctica/epica_domec/edc3deuttemp2007.txt