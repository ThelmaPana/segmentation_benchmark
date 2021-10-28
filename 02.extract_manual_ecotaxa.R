#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Extract manual particles with taxo from Ecotaxa
# Date: 20/04/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

library(tidyverse)
library(ecotaxar)
library(reticulate)
library(parallel)


# Set output directory
output_dir <- "data/manual"
#output_dir <- "data_cc4/manual"

n_cores <- 12


## Extract particles from ecotaxa ----
#--------------------------------------------------------------------------#
# project number
projid <- as.integer(4520) # for CC7
#projid <- as.integer(4693) # for CC4 

# connect to db
db <- db_connect_ecotaxa()

# get project
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

# ignore objects which are detritus or othertocheck
obj <- obj %>% filter(!taxon %in% c("detritus", "othertocheck"))


## Compute particles position in avi files ----
#--------------------------------------------------------------------------#
# Read apeep particles props, get img name, avi file and frame nb
# Do this with pandas

# List all tar archives
tar_files <- list.files(path = "data/regular_apeep_def/particles/", pattern = ".tar", full.names = TRUE, recursive = TRUE)

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


## Save particle properties ----
#--------------------------------------------------------------------------#
# write a csv 
obj %>% write_csv(file = file.path(output_dir, "02.ecotaxa_export_test_set.csv"))  




