# segmentation_benchmark

Benchmark for `apeep` semantic segmentation and regular segmentation on ISIIS data.

## Structure

`data` contains all data for segmentation benchmark:
- `manual`: ground truth data
    - `stacks`: manual stacks
    - `segmented`: manual particles for Ecotaxa import from manual stacks
    - `particles`: manual segments generated from manual stacks
- `regular_apeep`: `apeep` output for regular segmentation 
    - `segmented`: segmented images from `apeep` regular segmentation
    - `particles`: particles from `apeep` regular segmentation
- `semantic_apeep`: `Apeep` output for semantic segmentation
    - `segmented`: segmented images from `apeep` semantic segmentation
    - `particles`: particles from `apeep` semantic segmentation

`lib` contains needed scripts.

## Scripts
- `00.process_manual_stacks.py`: process manual stacks by extracting and measuring particles for Ecotaxa import, and generate segmented images
- `01.extract_manual_ecotaxa.R`: extract manual particles with taxonomy from Ecotaxa
- `02.match_particles.py`: match manual particles with those from `apeep` regular and semantic
- `03.matches_stats.Rmd`: compute global statistics (precision and recall), taxon recall and size class recall for both segmentations

## Results
A benchmark report containing computed statistics is generated: `03.matches_stats.html`
