#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Add original properties to apeep particles
# Date: 31/08/2021  
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

library(tidyverse)
library(scales)
library(fuzzyjoin)
library(parallel)


## Read particles extracted from segmented images ----
#--------------------------------------------------------------------------#

output_dir <- "data_cc4/matches"
apeep_parts_seg <- read_csv(file.path(output_dir, "reg_particles_props.csv"), col_types = cols()) %>% 
  rename( 
    bbox0 = `object_bbox-0`,
    bbox1 = `object_bbox-1`,
    bbox2 = `object_bbox-2`,
    bbox3 = `object_bbox-3`,
    area = object_area
  ) %>% 
  select(-object_label)


## Read original particles from apeep ----
#--------------------------------------------------------------------------#

# List tsv files of particles
tsv_files <- list.files("data_cc4/apeep_cc4_er2/particles", pattern = ".tsv", recursive=TRUE, full.names = TRUE)

# Extract columns names
col_names <- read_tsv(file = tsv_files[1], col_types = cols()) %>% colnames()

# Loop over tsv files and read them
apeep_parts <- tsv_files %>%
  map_df(~read_tsv(., skip=2, col_names = col_names,  col_types = cols(object_date = col_character(), object_time = col_character()))) 

# Clean column names
apeep_parts <- apeep_parts %>% 
  rename_with(~ gsub("object_", "", .x, fixed = TRUE)) %>% 
  rename( 
    bbox0 = `bbox-0`,
    bbox1 = `bbox-1`,
    bbox2 = `bbox-2`,
    bbox3 = `bbox-3`
  ) %>% 
  mutate(acq_id = str_split_fixed(img_file_name, "/", n=2)[,1], .after=img_file_name) # generate acq_id (apeep image name)

# Keep only particles from manually segmented images
apeep_parts <- apeep_parts %>% filter(acq_id %in% unique(apeep_parts_seg$acq_id))


## Join apeep properties on particles from segments ----
#--------------------------------------------------------------------------#
# Create fuzzy matching functions based on bbox
match_bbox <- function(v1, v2) {
  dist <- abs(v1 - v2)
  max_dist <- 2 # max acceptable distance between bbox border position
  ret <- data.frame(include = (dist <= max_dist))
  ret
}

# Parallel matching on bbox for each acq_id
matchl <- mclapply(unique(apeep_parts$acq_id), function(acq) {
  
  # Get particles from this image
  parts <- apeep_parts %>% filter(acq_id == acq) %>% select(contains("bbox"), avi_file, frame_nb, line_nb) %>% rename_with(~gsub("bbox", "orig_bbox", .x, fixed = TRUE), starts_with("bbox")) # rename bbox of original apeep particles to orig_bbox
  parts_seg <- apeep_parts_seg %>% filter(acq_id == acq)
  
  # Perform fuzzy match
  match <- fuzzy_left_join(
    parts_seg,
    parts,
    by = c(
      "bbox0" = "orig_bbox0",
      "bbox1" = "orig_bbox1",
      "bbox2" = "orig_bbox2",
      "bbox3" = "orig_bbox3"
    ),
    match_fun = list(match_bbox, match_bbox, match_bbox, match_bbox)
  )
  return(match)
}, mc.cores=36) # on 24 cores
# this returns a list, recombine it into a tibble
all_match <- do.call(bind_rows, matchl) 

# Some particles were not matched
not_match <- all_match %>% filter(is.na(avi_file)) %>% select(object_id:area)
message(nrow(not_match), " particles could not be matched with original apeep particles")

# Write csv
write_csv(all_match %>% select(-contains("orig_bbox")), file = file.path(output_dir, "reg_particles_props_avi.csv"))

