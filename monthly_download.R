#-----------------------------------------------------------------------------#
# OFAC Lists: Monthly Download
# Last updated 2022-04-29
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
sdn_df <- sdn %>% 
  dplyr::full_join(sdn_add) %>% 
  dplyr::full_join(sdn_alt) %>% 
  dplyr::full_join(sdn_comments) %>% 
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
cons_df <- cons %>% 
  dplyr::full_join(cons_add) %>% 
  dplyr::full_join(cons_alt) %>% 
  dplyr::full_join(cons_comments) %>% 
  dplyr::mutate(Program_cat = "NSDN")

rm(cons, cons_add, cons_alt, cons_comments)


# OFAC --------------------------------------------------------------------

ofac_df <- rbind(sdn_df, cons_df)

ofac_df$Date <- Sys.Date()

# Save full ofac lists file
save(ofac_df, file = paste0("data/ofac_full_", Sys.Date(), ".RData"))

# Save more minimal file focusing on locations and programs
ofac_loc <- ofac_df %>% 
  dplyr::select(Ent_num, SDN_name, SDN_type, Program, 
                Country, Program_cat, Date) %>% 
  dplyr::distinct()

saveRDS(ofac_loc, paste0("data/ofac_loc_", Sys.Date(), ".rds"))

# Save aggregated file
ofac_agg <- ofac_loc %>% 
  dplyr::group_by(Program_cat, Country) %>% 
  dplyr::summarize(Count = dplyr::n(), .groups = "drop") %>% 
  dplyr::ungroup() %>% 
  dplyr::mutate(Date = Sys.Date())

saveRDS(ofac_agg, paste0("data/ofac_agg_", Sys.Date(), ".rds"))
