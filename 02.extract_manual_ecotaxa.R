#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Extract manual particles with taxo from Ecotaxa
# Date: 20/04/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

library(tidyverse)
library(ecotaxar)
library(googlesheets4)
library(reticulate)
library(parallel)
library(data.tree)

gs4_auth(use_oob = TRUE)
1

# Set output directory
output_dir <- "data/manual"
#output_dir <- "data_cc4/manual"

n_cores <- 12

# link to aggregation spreadsheet
ss <- "https://docs.google.com/spreadsheets/d/10DbIrieAvBjVuB3Ub_gZoIqdOYVJJ3SaCvinsBghjMM/edit?usp=sharing"

## Extract particles from ecotaxa ----
#--------------------------------------------------------------------------#
# project number
projid <- as.integer(4520) # for CC7
#projid <- as.integer(4693) # for CC4 

# connect to db
db <- db_connect_ecotaxa(host="ecotaxa.obs-vlfr.fr", dbname="ecotaxa", user="zoo", password="z004ecot@x@")

# get project, samples and acquisitions
projects <- tbl(db, "projects") %>% filter(projid %in% !!projid) %>% select(projid, mappingobj) %>% collect()

# get taxo
taxo <- tbl(db, "taxonomy") %>% collect()

# get objects
obj <- tbl(db, "objects") %>% 
  filter(projid %in% !!projid) %>% 
  map_names(mapping = projects$mappingobj) %>% 
  left_join(tbl(db, "process") %>% select(processid, img_name = orig_id)) %>% # get image name from process
  select(object_id = orig_id, img_name, bbox0=`bbox-0`, bbox1=`bbox-1`, bbox2=`bbox-2`, bbox3=`bbox-3`, area, classif_id) %>% # keep object_id, image name, bbox and classif
  collect() %>% 
  mutate(
    taxon=taxo_name(classif_id, taxo=taxo, unique=TRUE),
    lineage=lineage(classif_id, taxo=taxo)
    ) %>% 
  select(-classif_id)

# disconnect from db
db_disconnect_ecotaxa(db)


## Compute bbox diagonal ----
#--------------------------------------------------------------------------#
obj <- obj %>% 
  mutate(diag_bbox = sqrt((bbox2 - bbox0)^2 + (bbox3 - bbox1)^2))


## Compute particles position in avi files ----
#--------------------------------------------------------------------------#
# Read apeep particles props, get img name, avi file and frame nb
# Do this with pandas

# List all tar archives
tar_files <- list.files(path = "data/regular_apeep/particles/", pattern = ".tar", full.names = TRUE, recursive = TRUE)

# Import python package
pd <- import("pandas")
tarfile <- import("tarfile")


# Parallel read of tsv files
reads <- mclapply(tar_files, function(file) {
  
  # Open tar archive
  arch <-  tarfile$open(file, mode = "r")
  
  # Get name of tsv file
  tsv_file_name <- arch$getnames() %>% str_subset(".tsv")
  
  # Read tsv file
  df <- pd$read_csv(arch$extractfile(tsv_file_name), sep = "\t", comment = "[") %>% 
    as_tibble() %>% 
    select(img_name = acq_id, avi_file = object_avi_file, frame_nb = object_frame_nb) %>% unique()
  
  # Close tar archive
  arch$close()
  
  return(df)
}, mc.cores=n_cores) 
# this returns a list, recombine it into a tibble
avi_files <- do.call(bind_rows, reads) 

# Compute relative frame within each image
avi_files <- avi_files %>% 
  arrange(avi_file, frame_nb) %>% 
  group_by(avi_file) %>% 
  mutate(frame_img = row_number() - 1) %>% 
  ungroup()


# Compute relative frame number and line number and join with avi file and true frame number
obj <- obj %>% 
  mutate(
    frame_img = bbox1 %/% 2048,  # frame number as bbox1 // 2048
    line_nb = bbox1 %% 2048, # line number as bbox1 modulo 2048
  ) %>%  
  left_join(avi_files, by = c("img_name", "frame_img")) %>% # join with avi file
  select(-frame_img) %>% 
  arrange(img_name, bbox1)


# Check consistency
obj %>% 
  filter(avi_file == unique(obj$avi_file)[1]) %>% 
  ggplot() +
  geom_point(aes(x = bbox1, y = line_nb, color = factor(frame_nb))) +
  geom_hline(yintercept = 2048) +
  xlim(0, 10240) + ylim(0, 2048)


## Build the tree ----
#--------------------------------------------------------------------------#
tc <- count(obj, taxon, lineage) %>% 
  # convert it into a tree
  rename(pathString=lineage) %>%
  arrange(pathString) %>%
  as.Node()

print(tc, "taxon","n", limit = 50)
# Convert to dataframe
tcd <- ToDataFrameTree(tc, "taxon", "n")%>% 
  as_tibble() %>% 
  rename(level0=taxon, nb_level0=n)


## Write tree into GSS ----
#--------------------------------------------------------------------------#
# Start by erasing previous data (3 first columns) in spreadsheet
range_flood(ss, sheet = "tcd", range = "tcd!A:C", reformat = FALSE)
# Write new tree
range_write(ss, data = tcd) 
# Open it in browser tab to make sure everything is ok
gs4_browse(ss)


## Read tree count from Google Spread Sheet (GSS) and create table for taxonomy match ----
#--------------------------------------------------------------------------#
tcd <- read_sheet(ss)

# Get match between level0 (EcoTaxa taxonomy), level1 (taxonomy to use for classif) and level2 (ecological group)
taxo_match <- tcd %>% 
  select(level0, level1, plankton) %>% 
  mutate(plankton = as.logical(plankton)) %>% 
  drop_na(level0)

# Raise an error if any line has missing taxa
stopifnot("At least one taxa is not associated with others" = !any(is.na(taxo_match)))


## Match taxonomy between EcoTaxa export and taxonomy to use ----
#--------------------------------------------------------------------------#
obj <- obj %>% 
  rename(level0=taxon) %>% 
  left_join(taxo_match, by = "level0") %>% 
  select(-level0) %>% 
  rename(taxon = level1) %>% 
  select(-c(lineage, plankton))

# Ignore objects in detritus or other_living
obj <- obj %>% filter(!taxon %in% c("detritus", "other_living"))


## Plot distribution per taxa ----
#--------------------------------------------------------------------------#
obj %>% 
  count(taxon) %>% 
  arrange(n) %>% 
  mutate(taxon = factor(taxon, levels = unique(taxon))) %>% 
  ggplot() +
  geom_col(aes(y = taxon, x = n)) 

length(unique(obj$taxon))


## Save particle properties ----
#--------------------------------------------------------------------------#
# write a csv 
obj %>% write_csv(file = file.path(output_dir, "02.ecotaxa_export_test_set.csv"))  

