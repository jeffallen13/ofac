#-----------------------------------------------------------------------------#
# OFAC Lists: Monthly Download
# Last updated 2024-10-31
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
sdn <- read.csv(
  "https://www.treasury.gov/ofac/downloads/sdn.csv", 
  header = FALSE, col.names = main.names) %>% 
  # remove placeholder line at end of each file
  dplyr::filter(SDN_name != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

sdn_add <- read.csv(
  "https://www.treasury.gov/ofac/downloads/add.csv", 
  header = FALSE, col.names = add.names) %>% 
  dplyr::filter(Address != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

sdn_alt <- read.csv(
  "https://www.treasury.gov/ofac/downloads/alt.csv", 
  header = FALSE, col.names = alt.names) %>% 
  dplyr::filter(Alt_name != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

sdn_comments <- 
  read.csv("https://www.treasury.gov/ofac/downloads/sdn_comments.csv", 
           header = FALSE, col.names = comments.names) %>% 
  dplyr::filter(Remarks_cont != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

# Check for Ent_num NAs
sum(is.na(sdn$Ent_num))
sum(is.na(sdn_add$Ent_num))
sum(is.na(sdn_alt$Ent_num))
sum(is.na(sdn_comments$Ent_num))

# Join
## Many-to-many: Cartesian product
sdn_df <- sdn %>% 
  dplyr::left_join(sdn_add) %>% 
  dplyr::left_join(sdn_alt, relationship = "many-to-many") %>% 
  dplyr::left_join(sdn_comments) %>% 
  dplyr::mutate(Program_cat = "SDN")

rm(sdn, sdn_add, sdn_alt, sdn_comments)


# Non-SDN -----------------------------------------------------------------

# Import
cons <- read.csv(
  "https://www.treasury.gov/ofac/downloads/consolidated/cons_prim.csv", 
  header = FALSE, col.names = main.names) %>% 
  # remove placeholder line at end of each file
  dplyr::filter(SDN_name != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

cons_add <- read.csv(
  "https://www.treasury.gov/ofac/downloads/consolidated/cons_add.csv", 
  header = FALSE, col.names = add.names) %>% 
  dplyr::filter(Address != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

cons_alt <- read.csv(
  "https://www.treasury.gov/ofac/downloads/consolidated/cons_alt.csv", 
  header = FALSE, col.names = alt.names) %>% 
  dplyr::filter(Alt_name != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

cons_comments <- read.csv(
  "https://www.treasury.gov/ofac/downloads/consolidated/cons_comments.csv", 
  header = FALSE, col.names = comments.names) %>% 
  dplyr::filter(Remarks_cont != "") %>%  
  dplyr::mutate(Ent_num = as.integer(Ent_num))

# Check for Ent_num NAs
sum(is.na(cons$Ent_num))
sum(is.na(cons_add$Ent_num))
sum(is.na(cons_alt$Ent_num))
sum(is.na(cons_comments$Ent_num))

# Join
## Many-to-many: Cartesian product
cons_df <- cons %>% 
  dplyr::left_join(cons_add) %>% 
  dplyr::left_join(cons_alt, relationship = "many-to-many") %>% 
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
