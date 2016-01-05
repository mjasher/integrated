## Author: Baihua Fu
## Created: 17 Jun 2013

## Input requirements:
# 1. Commence to Flow levels with flooding thresholds and event thresholds (default:ctf_dss.csv, in "\\Inputs" folder)
# 2. Index curves and weights for each modelled species, in "\\Input\\index" folder
# 3. Hydrological inputs, including flow data for river gauges (defined in ctf_dss.csv), and groundwater data. In "\\Inputs\\[Scenario Name]" folder. Default with Historical flow and groundwater scenario.



#setwd("C:\\UserData\\fub\\work09\\Namoi\\Model_dss")
setwd("C:\\UserData\\takuyai\\ownCloud\\integrated\\Modules\\Ecology\\Namoi_DSS")
library(zoo) # time series
library(hydromad) # version 0.9-8
library(ggplot2) # plotting


#################################
###  Hydrological indicators  ###
#################################

## Function to calculate cease-to-flow days (annual).
cease.days <- function (x,...){
  ceaseflow <- function (x, ...) {
    zerodays <- sum(x == 0, na.rm = T)
    }
  summaryby <- as.POSIXlt(time(x))$year + 1900
  cease <- aggregate(x, by=summaryby, FUN = ceaseflow)
  return(cease)
}


## Function to calculate median/total flow/baseflow levels (annual), if total, fun=sum.
flowsum <- function (x,fun=median,...){
  summaryby <- as.POSIXlt(time(x))$year + 1900
  flowsummary <- aggregate(x, by=summaryby, FUN = fun, na.rm=TRUE)
  return(round(flowsummary,2))
}


## Function to calculate yearly number of days above CTF levels. Input (x) is surfaceflow.
ctf.days <- function (x, ctf = 4000, ...){
  flooddays <- function (x, ...)  {
    days <- sum(x > ctf, na.rm = T)
    return(days)
  }
  summaryby <- as.POSIXlt(time(x))$year + 1900
  ctfdaysyear <- aggregate(x, by=summaryby, FUN = flooddays)
  return(ctfdaysyear)
}


## Function to calculate annual averaged number of overflow (flow above a threshold) events. Input (x) is surfaceflow
## By default, the minimum number of days that can separate events is 5 days,
## and the minimum number of days in each event window is 1 day.
ctf.events <- function (x, ctf = 4000, gap = 5, minduration = 1, ...){
  flowevent <- eventseq(x, thresh = ctf, mingap = gap, mindur=minduration)
  floweventinfo <- eventinfo(x, flowevent, FUN=mean)
  annualevent <- aggregate(Value ~ Yearmid, data=floweventinfo, FUN=length)
  eventyear <- as.POSIXlt(as.Date(as.character(annualevent[,1]), format="%Y"))$year+1900
  annualeventzoo <- zoo(annualevent[,2],eventyear)
  return(annualeventzoo)
}


################################
###  Ecological indicators  ####
################################

## Function to generate index curve for flood timing.
cpttiming <- function(monthinput, species = "RRGMS", ...){
  timeindex <- approxes[[sprintf("%s_timing.csv", species)]](monthinput)
  return(round(timeindex,1))
}

## Function to generate index curve for flood duration.
cptduration <- function(durationinput, species = "RRGMS", ...){
  durationindex <- approxes[[sprintf("%s_duration.csv", species)]](durationinput)
  return(round(durationindex,1))
}

## Function to generate index curve for interflood dry period.
cptdry <- function(dryinput, species = "RRGMS", ...){
  dryindex <- approxes[[sprintf("%s_dry.csv", species)]](dryinput)
  return(round(dryindex,1))
}

## Function to calculate weighted index.
cptweight <- function(tindex=1, durindex=1, dryindex=1, species = "RRGMS",...){
  wtime <- subset(weightall, Species == species)[,2]
  wdur <- subset(weightall, Species == species)[,3]
  wdry <- 1-wtime-wdur
  #indexsum <- exp(log(tindex)*wtime + log(durindex)*wdur + log(dryindex)*wdry) # weighted geometric mean
  indexsum <- tindex*wtime + durindex*wdur + dryindex*wdry
  return(round(indexsum,1))
}


## Function to generate event summary.
### A little extra code to fix a bug in the Hydromad package for estimating inter flood dry period.
preInterEventDuration <- function(evq)
{
    if (inherits(evq, "zoo"))
        stopifnot(is.regular(evq, strict = TRUE))
    interCounter <- cumsum(is.na(coredata(evq)))
    vals <- tapply(interCounter, coredata(evq), FUN = head,1)
    c(vals[1], diff(vals))
}

### Modify the eventinfo function in the Hydromad package for additional and rearranged outputs.
eventinfo <- function (X, events, FUN = mean, species="RRGMS",...)
{
    stopifnot(inherits(X, "zoo"))
    xValues <- eventapply(X, events = events, FUN = FUN, ...)
    xValuesend <- eventapply(X, events = events, FUN = FUN, TIMING = "end") ##New
    xLengths <- eventapply(X, events = events, FUN = NROW, TIMING = "middle",
        by.column = FALSE)
    midTimeComponents <- as.POSIXlt(time(xLengths)) ## mid time
    startTimeComponents <- as.POSIXlt(time(xValues)) ## start time
    Monthstart = startTimeComponents$mon + 1  ## start time
    Duration = coredata(xLengths)
    DryPeriod = preInterEventDuration(events)
    TimeIndex = cpttiming(Monthstart, species=species) ##start time
    DurationIndex = cptduration(coredata(xLengths), species=species)
    DryIndex = cptdry(preInterEventDuration(events), species=species)
    Indexsum = cptweight(tindex=TimeIndex, durindex=DurationIndex, dryindex=DryIndex, species = species)
    data.frame(StartTime = time(xValues), EndTime = time(xValuesend), Value = coredata(xValues),  #EndTime new
        Yearmid = midTimeComponents$year + 1900, Monthstart = Monthstart,
        Duration = Duration, DryPeriod = DryPeriod,
        TimeIndex = TimeIndex,
        DurationIndex = DurationIndex,
        DryIndex = DryIndex,
        Indexsum = Indexsum,
        Indexsumdays = Indexsum*Duration)
}


## Function to generate yearly index from daily sw+gw index data.
yearlysum.eco <- function (x,fun=sum,...){
  summaryby <- as.POSIXlt(time(x))$year + 1900
  flowsummary <- aggregate(x, by=summaryby, FUN = fun, na.rm=FALSE)
  return(round(flowsummary,2))
}

##  Function to calculate groundwater level index, inputs and outputs are daily data
cptgwlevel <- function(gwlevel, species = "RRGMS", ...){
  gwindex <- as.zoo(approxes[[sprintf("%s_gwlevel.csv", species)]](gwlevel))
  index(gwindex) <- index(gwlevel)
  return(round(gwindex,1))
}

##  Function to calculate groundwater salinity index
cptgwsalinity <- function(gwsalinity, species = "RRGMS", ...){
  gwsal <- approxes[[sprintf("%s_salinity.csv", species)]](gwsalinity)
  return(gwsal)
}

## Function to combine surface water (event-based) and groundwater indices (daily), using weighted average.
gswindex <- function(gwindex, swindex, surfaceflow, gswfun=weighted,...)
{
  ext <- function(d) {
    if (d < head(index(surfaceflow), n=1) | d > tail(index(surfaceflow), n=1)) {
      return(NA)
    } else {
    date.falls.in.range <- which(d >= swindex$StartTime & d <= swindex$EndTime)
    if (length(date.falls.in.range) == 0) {
      return(0)
    } else {
    swindex$Indexsum[date.falls.in.range]
    }
  }
}
  swindex.ext <- sapply(index(gwindex), ext)
  indexall <- merge(gwindex, swindex.ext)
  weighted <- function(d) d[1]*gweight + d[2]*(1-gweight)
  indexall$ecoindex <- apply(indexall,1,FUN=gswfun)
  return(indexall$ecoindex)
}


############################
###  Generating outputs  ###
############################
## Function to generate indices for each scenario
envindex <- function(assetid, scenario = "S1", ecospecies= c("RRGMS", "RRGRR"), ...){
  ## read in data
  gauge <- asset.table[assetid,2] #first row is associated with the first asset and so on.
  surfaceflow <- hydroinputlist[[paste(gauge,".csv",sep="")]][,1]
  baseflow <- hydroinputlist[[paste(gauge,".csv",sep="")]][,2]
  ## generate gw level data
  gwlevel <- hydroinputlist[["gwlevel.csv"]][,assetid] #first column is associated with first asset and so on.
  ## generate hydrological index
  gw.mean <- flowsum(gwlevel, fun=mean)
  baseflow.median <- flowsum(baseflow, fun=median)
  ceaseflow.day <- cease.days(surfaceflow)
  totalflow <- flowsum(surfaceflow, fun=sum)
  ctf.low.days <- ctf.days(surfaceflow,ctf=asset.table[assetid,4])
  ctf.low.events <- ctf.events(surfaceflow, ctf=asset.table[assetid,4], gap=5, minduration=1) 
  ctf.mid.days <- ctf.days(surfaceflow,ctf=asset.table[assetid,5])
  ctf.mid.events <- ctf.events(surfaceflow, ctf=asset.table[assetid,5], gap=5, minduration=1)
  ctf.high.days <- ctf.days(surfaceflow,ctf=asset.table[assetid,6])
  ctf.high.events <- ctf.events(surfaceflow, ctf=asset.table[assetid,6], gap=5, minduration=1)
  ## generate ecological index
  flowevent <- eventseq(surfaceflow, thresh = asset.table[assetid,7], mingap = asset.table[assetid,8], mindur=asset.table[assetid,9])
  floweventinfo<-list()
  gwinfo<-list()
  allindex<-list()
  yearlyindex<-list()
  for (k in 1:length(ecospecies)){
    floweventinfo[[k]] <- eventinfo(surfaceflow, flowevent, FUN=mean, species=ecospecies[k])
    gwinfo[[k]] <- cptgwlevel(gwlevel, species=ecospecies[k])
    gwsalinity <- 10000 ## assumed salinity level is constantly 10000ppm, can be replaced with daily data.
    gwinfo[[k]] <- gwinfo[[k]]*cptgwsalinity(gwsalinity, species = ecospecies[k])
    allindex[[k]] <- gswindex(gwindex=gwinfo[[k]],swindex=floweventinfo[[k]], surfaceflow = surfaceflow) 
    yearlyindex[[k]] <- yearlysum.eco(allindex[[k]],fun=sum)
    }	
  eco<-yearlyindex[[1]]
  for (m in 2:length(yearlyindex)){
    eco<- merge.zoo(eco, yearlyindex[[m]],fill=NA)## change to fill=NA, 7/3/2013
  }
  names(eco)<-ecospecies
  ## combine all results
  index.all <- merge.zoo(gw.mean, baseflow.median, ceaseflow.day, totalflow,fill=NA) ## fill =NA because no data
  index.all <- merge.zoo(index.all, ctf.low.days, ctf.low.events, ctf.mid.days, ctf.mid.events,ctf.high.days, ctf.high.events,fill=0)	
	## fill=0 because when there is no recorded event, then it should be "0"
  index.all <- merge.zoo(index.all, eco, fill=NA) ## adding "fill=0", 10/8/2012. ## change to fill=NA, because if no eco, then it's no data. 7/3/2013
  colnames(index.all) <- c("Mean_gwlevel", "Med_baseflow", "Ceaseflow_days", "Totalflow", "CTFlow_days", "CTFlow_events", "CTFmid_days",
    "CTFmid_events", "CTFhigh_days", "CTFhigh_events", ecospecies)
  return(index.all)
}


##########################
###  Run  scenario(s)  ###
##########################

## Read in input data
## read in all breakpoint files
indexes <- lapply(dir("Inputs\\index", pattern=".csv", full.names=T), read.csv, header=T)
names(indexes) <- dir("Inputs\\index", pattern=".csv")
## read in asset table
asset.table <- read.csv("Inputs\\ctf_dss.csv", header=T)
## read in weights
weightall <- read.csv("Inputs\\index\\weight\\weight.csv", header=T)

### create a list of functions for each cpt
approxes <- lapply(indexes, function(cpt) approxfun(cpt[,1], cpt[,2], rule=2))

## Set up additional parameters:
## Set up weight for groundwater index
gweight = 0.2
## Set up scenarios and species to run
scenariolist <- c("Hist")
specieslist <- c("RRGMS", "RRGRR", "BBMS", "BBRR", "LGMS", "LGRR", "WCMS", "WCRR") ## For DSS, can use RRGMS only as a minimum.


## Run scenarios, outputs are stored in "\\Outputs\\[Scenario Name]\\"
for (i in 1:length(scenariolist)){
	## Create folders to store outputs for each scenario
	dir.create(paste("Outputs\\", scenariolist[i], sep="")) ## override previous outputs of same scenario name.
  ### read in hydrology data
  hydroinputlist <- lapply(dir(paste("Inputs\\", scenariolist[i], sep=""), pattern=".csv", full.names=T), read.zoo, header=T, sep=",")
  names(hydroinputlist) <- dir(paste("Inputs\\", scenariolist[i], sep=""), pattern=".csv") 
	for (j in 1:length(asset.table[,1])){
        index.all <- envindex(assetid = j,scenario = scenariolist[i],ecospecies = specieslist, gswfun=weighted)
        write.zoo(index.all, file=paste("Outputs\\", scenariolist[i],"\\asset", j,".csv", sep=""),sep=",")
	}
  }

