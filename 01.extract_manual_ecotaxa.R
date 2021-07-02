#--------------------------------------------------------------------------#
# Project: segmentation_benchmark
# Script purpose: Extract manual particles with taxo from Ecotaxa
# Date: 20/04/2021
# Author: Thelma Panaiotis
#--------------------------------------------------------------------------#

library(tidyverse)
library(ecotaxar)

# project number
projid <- as.integer(4520)

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

# write a csv 
obj %>% write_csv(file = "data/manual/ecotaxa_export.csv")  

# disconnect from db
db_disconnect_ecotaxa(db)
