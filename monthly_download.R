#-----------------------------------------------------------------------------#
# OFAC Lists: Monthly Download
# Last updated 2023-02-28
#-----------------------------------------------------------------------------#

library(magrittr)


# Names -------------------------------------------------------------------

main.names <- c(
  "Ent_num", "SDN_name", "SDN_type", "Program", "Title", "Call_sign", 
  "Vess_type", "Tonnage", "GRT", "Vess_flag", "Vess_owner", "Remarks"
)

add.names <- c(
  "Ent_num", "Add_num", "Address", "Locality", "Country", "Add_remarks"
)

alt.names <- c(
  "Ent_num", "Alt_num", "Alt_type", "Alt_name", "Alt_remarks"
)

comments.names <- c("Ent_num", "Remarks_cont")


# SDN ---------------------------------------------------------------------

# Import
sdn <- read.csv("data-raw/sdall/sdn.csv", header = FALSE)
sdn_add <- read.csv("data-raw/sdall/add.csv", header = FALSE)
sdn_alt <- read.csv("data-raw/sdall/alt.csv", header = FALSE)
sdn_comments <- read.csv("data-raw/sdall/sdn_comments.csv", header = FALSE)

# Apply var names
colnames(sdn) <- main.names
colnames(sdn_add) <- add.names
colnames(sdn_alt) <- alt.names
colnames(sdn_comments) <- comments.names

# Check summary
## Is Ent_num an integer? Sometimes there are special characters
summary(sdn)
summary(sdn_add)
summary(sdn_alt)
summary(sdn_comments)

# Join
## Many-to-many: Cartesian product
sdn_df <- sdn %>% 
  dplyr::left_join(sdn_add) %>% 
  dplyr::left_join(sdn_alt) %>% 
  dplyr::left_join(sdn_comments) %>% 
  dplyr::mutate(Program_cat = "SDN")

rm(sdn, sdn_add, sdn_alt, sdn_comments)


# Non-SDN -----------------------------------------------------------------

# Import
cons <- read.csv("data-raw/consall/cons_prim.csv", header = FALSE)
cons_add <- read.csv("data-raw/consall/cons_add.csv", header = FALSE)
cons_alt <- read.csv("data-raw/consall/cons_alt.csv", header = FALSE)
cons_comments <- read.csv("data-raw/consall/cons_comments.csv", header = FALSE)

# Apply var names
colnames(cons) <- main.names
colnames(cons_add) <- add.names
colnames(cons_alt) <- alt.names
colnames(cons_comments) <- comments.names

# Check summary
## Is Ent_num an integer? Sometimes there are special characters
summary(cons)
summary(cons_add)
summary(cons_alt)
summary(cons_comments)

# Join
## Many-to-many: Cartesian product
cons_df <- cons %>% 
  dplyr::left_join(cons_add) %>% 
  dplyr::left_join(cons_alt) %>% 
  dplyr::left_join(cons_comments) %>% 
  dplyr::mutate(Program_cat = "NSDN")

rm(cons, cons_add, cons_alt, cons_comments)


# OFAC --------------------------------------------------------------------

ofac_full <- rbind(sdn_df, cons_df)

ofac_full$Rep_date <- Sys.Date()

# Save full ofac lists file
save(ofac_full, file = paste0("data/ofac_full_", Sys.Date(), ".RData"))

# Narrower file; Uniqueness: Ent_num, program, country 
## Note that there can be multiple addresses/localities per country; thus, avoiding
ofac_prog_loc <- ofac_full %>% 
  dplyr::select(Ent_num, SDN_name, SDN_type, 
                Program, Program_cat, Country, Rep_date) %>% 
  dplyr::distinct()

saveRDS(ofac_prog_loc, paste0("data/ofac_prog_loc_", Sys.Date(), ".rds"))

# Narrower file; Uniqueness: Ent_num, country
## Entities can be on different lists
ofac_loc <- ofac_full %>% 
  dplyr::select(Ent_num, SDN_name, SDN_type, Country, Rep_date) %>% 
  dplyr::distinct()

saveRDS(ofac_loc, paste0("data/ofac_loc_", Sys.Date(), ".rds"))

# Aggregated count file
ofac_agg <- ofac_loc %>% 
  dplyr::group_by(Country, Rep_date) %>% 
  dplyr::summarize(Count = dplyr::n(), .groups = "drop") %>% 
  dplyr::ungroup()

saveRDS(ofac_agg, paste0("data/ofac_agg_", Sys.Date(), ".rds"))
